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

        def to_string(self):
            sequence = (self.name, self.desc, self.image)
            return '&'.join(sequence)

    def __init__(self):
        self.evidences = []
        # putting in "defense" or "prosecution" will show it for those benches
        self.poses = {'defense': ['def', 'hld'], 'prosecution': ['pro', 'hlp']}

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
        elevated_perms = client.is_cm or client.is_gm or client.is_mod
        if not elevated_perms:
            if client.is_blind:
                return False
            # TODO: check if this piece of evidence is 'translucent' (bypasses darkness)
            if not client.area.lights:
                return False
            if evi.pos == "all" or \
              client.pos == evi.pos or \
              client.pos in self.poses[evi.pos]:
                return True
        return True

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

    def add_evidence(self, client, name, description, image, pos='all'):
        if self.login(client):
            if client.area.evidence_mod == 'FFA':
                pos = 'hidden'
            self.evidences.append(self.Evidence(name, description, image, pos))

    def evidence_swap(self, client, id1, id2):
        if self.login(client):
            self.evidences[id1], self.evidences[id2] = self.evidences[id2], self.evidences[id1]

    def create_evi_list(self, client):
        evi_list = []
        nums_list = [0]
        for i in range(len(self.evidences)):
            if client.area.evidence_mod == 'FFA' and (client.is_cm or client.is_gm or client.is_mod):
                nums_list.append(i + 1)
                evi = self.evidences[i]
                evi_list.append(self.Evidence(evi.name, '<owner={}>\n{}'.format(
                    evi.pos, evi.desc), evi.image, evi.pos).to_string())
            elif self.evidences[i].pos != "hidden":
                if self.evidences[i].pos == "all" or \
                  client.pos == self.evidences[i].pos or \
                  client.pos in self.poses[self.evidences[i].pos]:
                    nums_list.append(i + 1)
                    evi_list.append(self.evidences[i].to_string())
        return nums_list, evi_list

    def del_evidence(self, client, evi_id):
        if self.login(client):
            self.evidences.pop(evi_id)

    def edit_evidence(self, client, evi_id, arg):
        if self.login(client):
            if client.area.evidence_mod == 'FFA' and self.correct_format(client, arg[1]):
                self.evidences[evi_id] = self.Evidence(arg[0], arg[1][14:], arg[2], arg[1][9:12])
                return
            if client.area.evidence_mod == 'FFA':
                client.send_ooc("""
You entered a bad pos - evidence hidden!
Make sure to have <owner=pos> at the top, where "pos" is the /pos this evidence should show up in.
Put in "all" if you want it to show up in all pos, or "hidden" for no pos.
""")
                arg[3] = "hidden"
            self.evidences[evi_id] = self.Evidence(arg[0], arg[1], arg[2], arg[3])
