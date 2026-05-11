# TsuserverDR, server software for Danganronpa Online based on tsuserver3,
# which is server software for Attorney Online.
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com> (original tsuserver3)
#           (C) 2018-22 Chrezm/Iuvee <thechrezm@gmail.com> (further additions)
#           (C) 2022 Tricky Leifa (further additions)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

class EvidenceList:
    class Evidence:
        def __init__(self, name, desc, image, pos):
            self.name = name
            self.desc = desc
            self.image = image
            self.pos = pos

        def set_name(self, name):
            self.name = name

        def set_desc(self, desc):
            self.desc = desc

        def set_image(self, image):
            self.image = image

        def to_tuple(self):
            sequence = (self.name, self.desc, self.image)
            return sequence

        def to_dict(self):
            return {
                "name": self.name,
                "desc": self.desc,
                "image": self.image,
                "pos": self.pos,
            }

    def __init__(self):
        self.evidences = []

    def import_evidence(self, data):
        for evi in data:
            name, desc, image, pos = "<name>", "<desc>", "", "all"
            if "name" in evi:
                name = evi["name"]
            if "desc" in evi:
                desc = evi["desc"]
            if "image" in evi:
                image = evi["image"]
            if "pos" in evi:
                pos = evi["pos"]
            self.evidences.append(self.Evidence(
                name, desc, image, pos))

    def export_evidence(self):
        return [e.to_dict() for e in self.evidences]

    def login(self, client):
        """
        Determine whether or not evidence can be modified.
        :param client: the client

        """
        elevated_perms = client.is_cm or client.is_gm or client.is_mod
        # HiddenCM is deprecated and merged into FFA
        if client.area.evidence_mod == "HiddenCM":
            client.area.evidence_mod = "FFA"
        if client.area.evidence_mod == "FFA":
            return True
        elif client.area.evidence_mod == "Mods" and not client.is_mod:
            return False
        elif (
            client.area.evidence_mod == "CM"
            and not elevated_perms
        ):
            return False
        return True

    def visible(self, evi, client):
        """
        Determine whether or not evidence is visible.
        :param evi: the piece of evidence to check
        :param client: the client

        """
        if client.is_cm or client.is_gm or client.is_mod:
            return True
        if client.is_blind:
            return False
        # TODO: check if this piece of evidence is 'translucent' (bypasses darkness)
        if not client.area.lights:
            return False
        pos = client.pos.strip(" ")
        for p in evi.pos.strip(" ").split(","):
            if p == "all" or (pos != "" and pos == p):
                return True
        return False

    def correct_format(self, client, desc):
        """
        Check whether or not an evidence item contains a correct
        `<owner = [pos]>` metadata, if FFA mode is on.
        :param client: origin
        :param desc: evidence description

        """
        if client.area.evidence_mod != "FFA":
            return True
        # correct format: <owner=pos,pos,pos>\ndesc
        lines = desc.split("\n")
        cmd = lines[0].strip(" ")  # remove all whitespace
        if cmd[:7] == "<owner=" and cmd.endswith(">"):
            return True
        return False

    def parse_desc(self, desc):
        # Remember to adjust this any time you add a new property
        num_properties = 1
        
        lines = desc.split("\n", num_properties)
        poses = "hidden"
        matches = 0
        for line in lines:
            cmd = line.strip(" ") # remove all whitespace
            if cmd.startswith("<") and cmd.endswith(">"):
                args = cmd.strip("<>").split("=")
                if len(args) < 2:
                    break
                key, value = args
                if key == "owner":
                    if value == "":
                        value = "hidden"
                    poses = value
                    matches += 1
        # Remvoes N lines, where N is how many <> we matched. Can't be more than 3.
        while matches > 0:
            # Truncates from the start of newline
            desc = desc[desc.find("\n")+1:]
            matches -= 1
        return desc, poses

    def add_evidence(self, client, name, description, image, pos='all'):
        if self.login(client):
            if (client.is_cm or client.is_gm or client.is_mod):
                pos = 'hidden'
            self.evidences.append(self.Evidence(name, description, image, pos))

    def evidence_swap(self, client, id1, id2):
        if self.login(client):
            self.evidences[id1], self.evidences[id2] = self.evidences[id2], self.evidences[id1]

    def create_evi_list(self, client):
        evi_list = []
        nums_list = [0]
        for i in range(len(self.evidences)):
            if (client.is_cm or client.is_gm or client.is_mod):
                nums_list.append(i + 1)
                evi = self.evidences[i]
                evi_list.append(self.Evidence(evi.name, '<owner={}>\n{}'.format(
                    evi.pos, evi.desc), evi.image, evi.pos).to_tuple())
            elif self.visible(self.evidences[i], client):
                nums_list.append(i + 1)
                evi_list.append(self.evidences[i].to_tuple())
        return nums_list, evi_list

    def del_evidence(self, client, evi_id):
        if self.login(client):
            self.evidences.pop(evi_id)

    def edit_evidence(self, client, evi_id, arg):
        if self.login(client):
            name = arg[0]
            desc = arg[1]
            image = arg[2]
            pos = arg[3]
            if self.correct_format(client, desc):
                desc, pos = self.parse_desc(desc)
                self.evidences[evi_id] = self.Evidence(name, desc, image, pos)
                return
            if (client.is_cm or client.is_gm or client.is_mod):
                client.send_ooc("""
You entered a bad pos - evidence hidden!
Make sure to have <owner=pos> at the top, where "pos" is the /pos this evidence should show up in.
Put in "all" if you want it to show up in all pos, or "hidden" for no pos.
""")
                pos = "hidden"
            self.evidences[evi_id] = self.Evidence(name, desc, image, pos)
