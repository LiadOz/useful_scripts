from clalit import ClalitScraper
from notifications import Notify
import time

SMILE_CLINIC = "865179"
D_DOCTOR_CODE = "91"
D_HYGINE_CODE = "92"

if __name__ == '__main__':
    cl = ClalitScraper()
    notify = Notify()
    notify.send_notification("started scraping")
    while True:
        visits = cl.find_clinic_visit("DENTAL", D_HYGINE_CODE, SMILE_CLINIC)
        if visits:
            print(visits)
            notify.send_notification("found visit")
            break
        time.sleep(60 * 10)
