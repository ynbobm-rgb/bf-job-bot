import time
import platform
from bot import scan
from storage import *

if __name__ == "__main__":
    sd = platform.system().lower()
    cs = "linux windows macos"
    
    if  sd in cs:
        while True:
            try:
                limit()
                scan()
            except Exception as e:
                log_securite("Crash-Bot", str(e), "N/A")
                print(e)
                time.sleep(900) # tous les 15 min
    else:
        try:
            limit()
            scan()
        except Exception as e:
            log_securite("Crash-Bot", str(e), "N/A")
            print(e)

