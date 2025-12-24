
'''
TODO:
- Remove songsArray. Use just the "allsongs" method
- Implement the cursor-like navigation
- Fix problem loading allsongs method.
- Fix search
- Cursor navigation needs to:
    * Move between long distant itens on search (jump from 2000 to 3000)
    * Correclty play and queue current selected item
    * Jump into pages and stay at same index of array

Idea:
    - Make one big array with all songs
    - Strip it into 15 itens on listing
    - You store just the index (1-15) and the real value on a different variable


'''


import subprocess
from getkey import getkey, keys
import threading
import re
import os
from time import sleep

HELP = False
PAGE_SIZE = 15
ACTIONS = {
    "NONE" :      " ",
    "EXIT" :      "&",
    "SEARCH" :    "?",
    "JUMPID" :    ":",
    "ACTION" :    ">"
}

class audTool():
    def __init__(self):
        super().__init__()

        self.startPageNumb = 1
        self.cursorPos = 0
        self.songsArray = [
            # {
                # songName:  str
                # songIndex: int
            # }
        ]
        self.allSongs = []
        self.results = []
        self.indexingSongs = True
        self.running = True

        self.action = ACTIONS["NONE"]
        self.generalInput = []

        subprocess.run("clear")

        self.loadList()

        # threading.Thread(target=self.loadAllSongs).start()
        threading.Thread(target=self.handleInput).start()
        threading.Thread(target=self.start).start().join()

        self.start()

    def start(self):
        while self.running:
            self.loadList() # Load info that will be printed with printInfo.
            print(f"\033[1J\n{self.printInfo()}", end="", flush=True) # prints the info.
            sleep(0.01)

    def execShell(self, command):
        output = subprocess.check_output(command, shell=True)
        output = output.decode("utf-8")
        return output

    def loadAllSongs(self):
        allSongsStr = self.execShell("audtool --playlist-display")
        allSongsArr = allSongsStr.split("\n")
        allSongsArr = allSongsArr[1:len(allSongsArr)-1]

        for i in allSongsArr:
            songName = re.search(r'(?<=\|).*(?=\|)', i)
            songIndex = re.search(r'\d+ (?=\|)', i)
            self.allSongs.append(
                {
                    "songName": songName.group(),
                    "songIndex": int(songIndex.group())
                }
            )

        self.indexingSongs = False

    def loadList(self):
        self.songAmmnt = int(self.execShell("audtool --playlist-length"))
        self.songsArray = [] # clear songsArray before updating it

        # Populate songsArray list
        lastIndex = PAGE_SIZE + self.startPageNumb-1
        i = self.startPageNumb
        while (i <= lastIndex):
            self.songsArray.append(
                {
                    "songName": self.execShell(f"audtool --playlist-song {i}").replace("\n", ""),
                    "songIndex": i
                }
            )
            i+=1

    def printInfo(self):
        info = []

        info.append("====== AUDTOOL-CLI ======")
        if (self.indexingSongs):
            info.append("Indexing all songs... Search not enabled.")

        shownArray = self.getCurrentArray()

        for i in shownArray:
            selected = False if i["songIndex"] != self.cursorPos else True

            info.append(f"{">" if selected else ""} {i["songIndex"]} - {i["songName"]}")

        info.append(f"Songs in Playlist: {self.songAmmnt}")
        info.append("")

        info.append(" ----- HELP ----- ")
        info.append(f" {ACTIONS["EXIT"]} -> Exits the program")
        info.append(f" {ACTIONS["JUMPID"]} -> Jump to this id on playlist")
        info.append(f" {ACTIONS["SEARCH"]} -> Search songs by name ({"Disabled" if self.indexingSongs else "Enabled"})")
        info.append(f" {ACTIONS["ACTION"]} -> Play or Queue the song (followed by a q or a p)")

        info.append(f"> {"".join(self.generalInput)}")
        info.append("\n")
        return "\n".join(info)

    def handleInput(self):
        while self.running:
            key = getkey()

            # match actions. Cannot be inside of a match-case.
            # for some reason ...
            if (key == ACTIONS["EXIT"]):
                os._exit(1)

            elif (key == ACTIONS["JUMPID"]) : # SEARCH BY ID
                self.generalInput.append(key)
                self.action = "JUMPID"

            elif (key == ACTIONS["SEARCH"]): # SEARCH BY STRING
                self.generalInput.append(key)
                if not self.indexingSongs:
                    self.action = "SEARCH"

            elif (key == ACTIONS["ACTION"]): # PLAY OR QUEUE
                self.generalInput.append(key)
                self.action = "ACTION"

            # Return if is an action.
            if (key in ACTIONS.values()):
                continue

            # Match case for fixed values.
            match key:
                # === MOVING LIST ===
                # --- moving one ---
                case keys.UP:
                    if(self.cursorPos > 1):
                        self.cursorPos -= 1
                case keys.DOWN:
                    if(self.cursorPos < len(self.getCurrentArray())):
                        self.cursorPos += 1
                # --- moving page ---
                case keys.RIGHT:
                    if(self.startPageNumb+PAGE_SIZE < self.songAmmnt):
                        self.startPageNumb += PAGE_SIZE
                    else:
                        self.startPageNumb = self.songAmmnt
                case keys.LEFT:
                    if(self.startPageNumb-PAGE_SIZE > 1):
                        self.startPageNumb -= PAGE_SIZE
                    else:
                        self.startPageNumb = 1

                case keys.BACKSPACE:
                    self.generalInput = self.generalInput[:-1]

                case _:
                    self.generalInput.append(key)

                    # Jump to ID
                    if (self.action == "JUMPID"):
                        idSearch = re.search(r'(?<=:)[1-9]\d*(?=\?|$)*', "".join(self.generalInput))
                        if idSearch:
                            idSearch = int(idSearch.group())

                            if(idSearch != None):
                                self.startPageNumb = idSearch
                    # Searching
                    elif (self.action == "SEARCH"):
                        search = re.search(r'(?<=\?)[^>:?]+(?=[>:?]|$)', "".join(self.generalInput))
                        if search:
                            search = str(search.group())

                            if(search != None):
                                self.results = [item for item in self.allSongs if search in item["songName"]]
                        pass

                    # Song action.
                    elif (self.action == "ACTION"):
                        if (key == 'q'):
                            # Add current selected song to queue
                            self.execShell(f"audtool --playqueue-add {self.cursorPos}")

                        elif (key == 'c'):
                            # Add current selected song to queue
                            self.execShell(f"audtool --playqueue-clear")

                        elif (key == 'p'):
                            # Play selected song
                            self.execShell(f"audtool playlist-jump {self.cursorPos} --playback-play")
                            pass


audTool()