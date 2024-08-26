import os
import time
import threading
import pyotp
import requests  # Required to make HTTP requests
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ANSI escape codes for colors
RESET = "\033[0m"
GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
YELLOW = "\033[33m"

def check_license():
    """Überprüfen Sie die Lizenzschlüssel-Validität."""
    print("Überprüfe Lizenz...")
    try:
        response = requests.get("https://pastebin.com/raw/YFHzZr1D")
        if response.status_code == 200 and response.text.strip() == "exoboti":
            print(f"{GREEN}Lizenz erfolgreich validiert.{RESET}")
            return True
        else:
            print(f"{RED}Ungültiger Lizenzschlüssel. Beenden...{RESET}")
            return False
    except Exception as e:
        print(f"{RED}Fehler bei der Überprüfung der Lizenz: {str(e)}{RESET}")
        return False

def read_file(file_path):
    """Reads a file and returns its content as a stripped string."""
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except Exception as e:
        print(f"{RED}Fehler beim Lesen der Datei {file_path}: {str(e)}{RESET}")
        return None

def initialize_driver(extension_path):
    """Initializes the Selenium driver with UC mode enabled."""
    try:
        print("Initialisiere Chrome mit aktiviertem UC-Modus...")
        driver = Driver(uc=True, extension_dir=extension_path)
        print("Chrome erfolgreich initialisiert.")
        return driver
    except Exception as e:
        print(f"{RED}Chrome fehlgeschlagen: {str(e)}{RESET}")
        return None

def read_credentials(file_path):
    """Reads email and password from a file."""
    credentials = read_file(file_path)
    if credentials:
        try:
            email, password = credentials.split("@")
            email = email + "@" + password.split()[0]
            password = password.split()[1]
            return email, password
        except Exception as e:
            print(f"{RED}Fehler beim Parsen der Anmeldedaten: {str(e)}{RESET}")
    return None, None

def read_cc_details(file_path):
    """Liest Kreditkartendaten aus einer Datei."""
    cc_details = read_file(file_path)
    if cc_details:
        try:
            cc_lines = cc_details.split("\n")
            kreditkartennummer, datum, cvv = cc_lines[0].split(",")
            vorname, nachname = cc_lines[1].split(",")
            strasse, hausnummer = cc_lines[2].split(",")
            plz, stadt = cc_lines[3].split(",")
            land = cc_lines[4]
            return (
                kreditkartennummer,
                datum,
                cvv,
                vorname,
                nachname,
                strasse,
                hausnummer,
                plz,
                stadt,
                land,
            )
        except Exception as e:
            print(f"{RED}Fehler beim Parsen der Kreditkartendaten: {str(e)}{RESET}")
    return None

def read_fiat_amounts(file_path):
    """Liest Fiat-Beträge aus einer Datei und gibt sie als Liste von Ganzzahlen zurück."""
    amounts = read_file(file_path)
    if amounts:
        try:
            return [int(amount) for amount in amounts.split("\n")]
        except Exception as e:
            print(f"{RED}Fehler beim Parsen der Fiat-Beträge: {str(e)}{RESET}")
    return []

def remove_first_line(file_path):
    """Removes the first line of the file."""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        with open(file_path, 'w') as file:
            file.writelines(lines[1:])
    except Exception as e:
        print(f"{RED}Fehler beim Entfernen der ersten Zeile: {str(e)}{RESET}")

def wait_for_user_or_timeout(timeout):
    """
    Wartet, bis der Benutzer die Eingabetaste drückt, oder bis eine festgelegte Zeitspanne abgelaufen ist, je nachdem, was zuerst eintritt.

    Parameter:
    timeout (int): Die Zeitspanne in Sekunden.
    """
    user_input_received = False

    def input_thread():
        nonlocal user_input_received
        input()
        user_input_received = True

    thread = threading.Thread(target=input_thread)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if user_input_received:
        print("Benutzer hat Enter gedrückt, fortfahren...")
    else:
        print(f"Slow down - alles menschlich - {timeout} Sekunden...")

def login(driver, email, password, shared_secret):
    """Melden Sie sich mit E-Mail, Passwort und TOTP beim Konto an."""
    try:
        login_url = "https://www.kucoin.com/de/ucenter/signin"
        driver.open(login_url)
        wait_for_user_or_timeout(3)

        driver.wait_for_element_visible(".KuxInput-input:nth-child(3)", timeout=60)
        driver.click(".KuxInput-input:nth-child(3)")
        driver.type(".KuxInput-input:nth-child(3)", email)
        wait_for_user_or_timeout(1)

        driver.wait_for_element_visible(".lrtcss-1nddmz0:nth-child(2)", timeout=60)
        driver.click(".lrtcss-1nddmz0:nth-child(2)")
        driver.type(".lrtcss-1nddmz0:nth-child(2)", password)
        wait_for_user_or_timeout(1)

        driver.wait_for_element_visible(".subButton", timeout=60)
        driver.click(".subButton")

        if shared_secret:
            totp = pyotp.TOTP(shared_secret)
            auth_code = totp.now()
            print(f"Authenticator-Code: {auth_code}")

            driver.wait_for_element_visible(".KuxInput-input.lrtcss-1a7r0qu", timeout=60)
            auth_code_digits = list(auth_code)
            input_fields = driver.find_elements(
                By.CSS_SELECTOR, ".KuxInput-input.lrtcss-1a7r0qu"
            )

            for input_field, digit in zip(input_fields, auth_code_digits):
                input_field.send_keys(digit)
            wait_for_user_or_timeout(7)
        else:
            wait_for_user_or_timeout(30)
            print(f"{YELLOW}Kein Authenticator-Code vorhanden, 30 sec warten.{RESET}")
            # Uncomment the following lines
            # driver.wait_for_element_visible(By.XPATH, '/html/body/div[1]/div/div/div/div/section/div/section/div/div[2]/div/div[1]/div/div/div/div/div/form/button', timeout=60)
            # driver.click(By.XPATH, '/html/body/div[1]/div/div/div/div/section/div/section/div/div[2]/div/div[1]/div/div/div/div/div/form/button')

        print(f"{GREEN}Erfolgreich eingeloggt!{RESET}")
        wait_for_user_or_timeout(7)
        return True
    except Exception as e:
        print(f"{RED}Anmeldung fehlgeschlagen: {str(e)}{RESET}")
        return False

def check_for_existing_plan(driver):
    """Überprüfen Sie den Status eines bestehenden wiederkehrenden Plans."""
    try:
        driver.open("https://www.kucoin.com/de/express/order_list?tab=recurring")
        time.sleep(5)

        status_element_xpath = '//*[@id="root"]/div/div[2]/div/div[2]/div[3]/div/div/div/div[1]/div/div/table/tbody/tr[1]/td[5]/div'

        try:
            status_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, status_element_xpath))
            )
            status_text = status_element.text.strip()

            if status_text == "Aktiv":
                print(f"{GREEN}Bestehender Plan ist aktiv.{RESET}")
                return True
            elif status_text == "in bearbeitung":
                print(f"{YELLOW}Plan wird bearbeitet. Warten auf 10 Minuten...{RESET}")
                wait_for_user_or_timeout(600)  # Warten Sie 10 Minuten oder überspringen Sie
                return check_for_existing_plan(driver)  # Überprüfen Sie den Planstatus nach dem Warten erneut
            elif status_text in ("Konnte nicht erstellt werden", "Storniert"):
                print(f"{YELLOW}Plan wurde nicht erstellt oder storniert. Kein aktiver Plan.{RESET}")
                return False
            else:
                print(f"{YELLOW}Unbekannter Status: {status_text}. Angenommen, kein aktiver Plan.{RESET}")
                return False
        except TimeoutException:
            print(f"{YELLOW}Kein Status gefunden. Angenommen, kein aktiver Plan.{RESET}")
            return False

    except Exception as e:
        print(f"{RED}Fehler beim Überprüfen der Pläne: {str(e)}{RESET}")
        return False

def remove_plan(driver):
    """Entfernen Sie den aktuellen Plan, bevor Sie einen neuen starten."""
    try:
        success = False
        retry_attempts = 3
        attempt = 0

        while not success and attempt < retry_attempts:
            attempt += 1
            print(f"{YELLOW}Versuch {attempt}, den Plan zu entfernen...{RESET}")

            details_pruefen_button = driver.find_element(
                By.XPATH,
                '//button[contains(@class, "KuxButton-root") and contains(@class, "KuxButton-contained") and contains(@class, "KuxButton-containedDefault") and contains(@class, "KuxButton-sizeMini") and contains(@class, "KuxButton-containedSizeMini") and contains(@class, "lrtcss-1oncvxu")]',
            )
            if details_pruefen_button:
                details_pruefen_button.click()
                wait_for_user_or_timeout(5)

            plan_kuendigen_button = driver.find_element(
                By.XPATH, "/html/body/div[7]/div/div[2]/div/div[2]/button[2]"
            )
            if plan_kuendigen_button:
                plan_kuendigen_button.click()
                wait_for_user_or_timeout(5)

            ja_abbrechen_button = driver.find_element(
                By.XPATH,
                '//button[contains(@class, "KuxButton-root") and contains(@class, "KuxButton-contained") and contains(@class, "KuxButton-containedPrimary") and contains(@class, "KuxButton-sizeBasic") and contains(@class, "KuxButton-containedSizeBasic") and contains(@class, "lrtcss-oiu68b")]',
            )
            if ja_abbrechen_button:
                ja_abbrechen_button.click()
                wait_for_user_or_timeout(5)

            email_code_senden_button = driver.find_element(
                By.XPATH,
                '//span[@id="__SEND_VCODE__EMAIL" and contains(@class, "ms_sendBtn___3JqQ1")]',
            )
            if email_code_senden_button:
                email_code_senden_button.click()
                print(f"{YELLOW}Warten auf Bestätigung per E-Mail - 60sec...{RESET}")
                wait_for_user_or_timeout(60)

            try:
                cancellation_confirmation = driver.find_element(
                    By.XPATH, '//div[@class="lrtcss-xac70s" and text()="Storniert"]'
                )
                if cancellation_confirmation:
                    print(f"{GREEN}Plan erfolgreich entfernt!{RESET}")
                    success = True
                    return True
            except NoSuchElementException:
                print(f"{YELLOW}Plan noch nicht entfernt, erneut versuchen...{RESET}")
                wait_for_user_or_timeout(3)

        if not success:
            print(f"{RED}Fehler beim Entfernen des Plans nach {retry_attempts} Versuchen.{RESET}")
            return False

    except Exception as e:
        print(f"{RED}Fehler beim Entfernen des Plans: {str(e)}{RESET}")
        return False

def remove_all_payment_methods(driver):
    """Entfernen Sie alle verfügbaren Zahlungsmethoden auf der Seite."""
    try:
        driver.get("https://www.kucoin.com/de/express/payment-method/bank-card")

        while True:
            try:
                delete_icon = driver.find_element(
                    By.CSS_SELECTOR, ".lrtcss-10whj87:nth-child(1) .ICDelete_svg__icon"
                )
                if delete_icon:
                    delete_icon.click()

                    confirm_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".KuxButton-contained"))
                    )

                    confirm_button.click()

                    try:
                        error_message = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "/html/body/div[8]/div[2]/div[1]/div[2]")
                            )
                        )
                        if error_message.is_displayed():
                            print(f"{RED}Karte kann nicht entfernt werden. Warte 10 Minuten, bevor du es erneut versuchst...{RESET}")
                            wait_for_user_or_timeout(600)
                            driver.refresh()
                            continue
                    except (NoSuchElementException, TimeoutException):
                        print(f"{GREEN}Keine Fehlermeldung erschienen. Fortfahren...{RESET}")

                    WebDriverWait(driver, 10).until_not(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, ".KuxDialog-mask"))
                    )

                    print(f"{GREEN}Zahlungsmethode erfolgreich entfernt.{RESET}")
                else:
                    break
            except NoSuchElementException:
                print(f"{GREEN}Keine weiteren Zahlungsmethoden zum Entfernen.{RESET}")
                break
            except ElementClickInterceptedException as e:
                print(f"{YELLOW}Elementklick abgefangen. Erneut versuchen...{RESET}")
                close_dialog(driver)
                continue
    except Exception as e:
        print(f"{RED}Fehler beim Entfernen der Zahlungsmethoden: {str(e)}{RESET}")

def close_dialog(driver):
    """Schließen Sie ein aktives Dialogfeld, das die Seite möglicherweise überlagert."""
    try:
        dialog_mask = driver.find_element(By.CSS_SELECTOR, ".KuxDialog-mask")
        if dialog_mask.0is_displayed():
            close_button = driver.find_element(By.CSS_SELECTOR, ".KuxButton-close")
            if close_button.is_displayed() and close_button.is_enabled():
                close_button.click()
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".KuxDialog-mask")
                    )
                )
                print(f"{GREEN}Dialogfeld erfolgreich geschlossen.{RESET}")
    except NoSuchElementException:
        print(f"{GREEN}Kein Dialogfeld-Overlay vorhanden.{RESET}")

def create_new_plan(
    driver,
    fiat_amount,
    kreditkartennummer,
    datum,
    cvv,
    vorname,
    nachname,
    strasse,
    hausnummer,
    plz,
    stadt,
    land,
):
    """Erstellen Sie einen neuen wiederkehrenden Plan."""
    success = False  # Flag zum Verfolgen, ob der Plan erfolgreich erstellt wurde

    while not success:
        try:
            # Verwenden Sie den fiat_amount im URL-Parameter
            initial_url = f"https://www.kucoin.com/de/express/recurring?fiatCurrency=EUR&cryptoCurrency=USDT&fiatAmount={fiat_amount}&recurringInfo%5Bfrequency%5D=DAILY&recurringInfo%5BtimeOfDay%5D=0&recurringInfo%5BtimeZone%5D=%2B2"
            print(f"Öffne die initiale URL: {initial_url}")
            driver.open(initial_url)
            wait_for_user_or_timeout(1)

            # Der Rest der Methode bleibt unverändert
            # Warten, bis das Element klickbar wird
            element_xpath = '//*[@id="root"]/div/div[2]/div/div[2]/div/div[1]/div/form/button'
            max_wait_time = 60
            start_time = time.time()

            print("Warten, bis das Element klickbar wird...")
            while time.time() - start_time < max_wait_time:
                try:
                    element = driver.find_element(By.XPATH, element_xpath)
                    if element.is_displayed() and element.is_enabled():
                        driver.execute_script("arguments[0].click();", element)
                        print(f"{GREEN}Element erfolgreich geklickt.{RESET}")
                        break
                except Exception as e:
                    print(f"{YELLOW}Element noch nicht klickbar: {str(e)}{RESET}")
                wait_for_user_or_timeout(1)

            wait_for_user_or_timeout(5)

            next_element_css_selector = ".lrtcss-1n5m7pa > div:nth-child(1)"
            try:
                print(f"Überprüfen, ob das Element {next_element_css_selector} sichtbar ist...")
                if driver.is_element_visible(next_element_css_selector):
                    element = driver.find_element(By.CSS_SELECTOR, next_element_css_selector)
                    driver.execute_script("arguments[0].click();", element)
                    print(f"{GREEN}Element {next_element_css_selector} ist vorhanden und wurde geklickt.{RESET}")
                else:
                    print(f"{RED}Element {next_element_css_selector} ist nicht vorhanden.{RESET}")
            except StaleElementReferenceException as e:
                print(f"{YELLOW}Veraltete Elementreferenz: {str(e)}{RESET}")
            except NoSuchElementException as e:
                print(f"{RED}Element nicht gefunden: {str(e)}{RESET}")

            wait_for_user_or_timeout(5)

            # Überprüfen, ob das Modal angezeigt wird, das auf einen bestehenden USDT-Plan hinweist
            existing_plan_modal = driver.find_elements(
                By.XPATH,
                '//div[@class="KuxModalHeader-title lrtcss-mm91cv" and text()="USDT Plan existiert bereits"]',
            )
            if existing_plan_modal:
                print(f"{YELLOW}USDT-Plan existiert bereits. Klicke auf 'Plan ansehen'...{RESET}")
                plan_ansehen_button = driver.find_element(
                    By.XPATH,
                    '//button[contains(@class, "KuxButton-root") and contains(@class, "KuxButton-outlined") and contains(@class, "KuxButton-outlinedPrimary") and contains(@class, "KuxButton-sizeBasic") and contains(@class, "KuxButton-outlinedSizeBasic") and contains(@class, "lrtcss-15x7h7v")]',
                )
                if plan_ansehen_button:
                    plan_ansehen_button.click()
                    print(f"{GREEN}'Plan ansehen' geklickt.{RESET}")
                    wait_for_user_or_timeout(5)
                    if remove_plan(driver):
                        continue  # Nach dem Entfernen des Plans erneut versuchen
                    else:
                        return False

            # Füllen Sie die Formularfelder aus
            print("Formularfelder ausfüllen...")
            vorname_field = driver.find_element(By.XPATH, '//*[@id="firstName"]/input')
            nachname_field = driver.find_element(By.XPATH, '//*[@id="lastName"]/input')
            kreditkartennummer_field = driver.find_element(
                By.XPATH, '//*[@id="cardNumber"]/input'
            )
            datum_field = driver.find_element(By.XPATH, '//*[@id="expireDate"]/input')
            cvv_field = driver.find_element(By.XPATH, '//*[@id="cvv"]/input')
            next_button = driver.find_element(
                By.XPATH,
                "/html/body/div[7]/div[2]/div[2]/div[1]/form/div/div[3]/div/div[2]/button",
            )

            vorname_field.click()
            vorname_field.send_keys(vorname)
            wait_for_user_or_timeout(1)
            nachname_field.click()
            nachname_field.send_keys(nachname)
            wait_for_user_or_timeout(1)
            kreditkartennummer_field.click()
            kreditkartennummer_field.send_keys(kreditkartennummer)
            wait_for_user_or_timeout(1)
            datum_field.click()
            datum_field.send_keys(datum)
            wait_for_user_or_timeout(1)
            cvv_field.click()
            cvv_field.send_keys(cvv)
            wait_for_user_or_timeout(1)
            next_button.click()
            wait_for_user_or_timeout(5)

            # Nächste Schritte
            wait_for_user_or_timeout(3)
            country_field = driver.find_element(By.XPATH, '//*[@id="country"]/div/div[2]')
            country_field.click()
            wait_for_user_or_timeout(5)
            input_country = driver.find_element(
                By.XPATH, '//*[@id="country"]/div/div[3]/input'
            )
            input_country.send_keys(land)
            wait_for_user_or_timeout(5)
            field = driver.find_element(
                By.XPATH, "/html/body/div[8]/div[1]/div/div/div/div/div"
            )
            field.click()
            wait_for_user_or_timeout(4)
            street_no_field = driver.find_element(By.XPATH, '//*[@id="streetNo"]/input')
            street_name_field = driver.find_element(By.XPATH, '//*[@id="streetName"]/input')
            zip_code_field = driver.find_element(By.XPATH, '//*[@id="postalCode"]/input')
            city_field = driver.find_element(By.XPATH, '//*[@id="city"]/input')
            street_no_field.click()
            street_no_field.send_keys(hausnummer)
            wait_for_user_or_timeout(2)
            street_name_field.click()
            street_name_field.send_keys(strasse)
            wait_for_user_or_timeout(1)
            zip_code_field.click()
            zip_code_field.send_keys(plz)
            wait_for_user_or_timeout(1)
            city_field.click()
            city_field.send_keys(stadt)
            wait_for_user_or_timeout(1)

            # Klicken Sie auf die Schaltfläche "Karte speichern" (früher als "final button" bezeichnet)
            final_button = driver.find_element(By.XPATH,
                                               '/html/body/div[7]/div[2]/div[2]/div[2]/form/div/div[3]/div/div[2]/button[2]')
            final_button.click()
            wait_for_user_or_timeout(5)

            # Überprüfen und finden Sie die richtige Kreditkarte anhand der letzten vier Ziffern
            last_four_digits = kreditkartennummer[-4:]
            credit_card_divs = driver.find_elements(By.CSS_SELECTOR, '.lrtcss-1ouop9m .__payment-label > div')
            for div in credit_card_divs:
                if last_four_digits in div.text:
                    div.click()
                    print(f"{GREEN}Klickte auf das Kreditkartendiv mit den letzten vier Ziffern: {last_four_digits}{RESET}")
                    break

            # Klicken Sie auf das Kontrollkästchen, um die Bedingungen zu akzeptieren, usw.
            checkbox_selector = '.KuxCheckbox-checkbox.lrtcss-157ll7t'
            driver.wait_for_element_visible(checkbox_selector, timeout=10)
            driver.click(checkbox_selector)
            wait_for_user_or_timeout(1)

            # Klicken Sie auf die endgültige Kauf-Schaltfläche, um den Vorgang abzuschließen
            try:
                button_selector = 'button.KuxButton-root:nth-child(2)'
                driver.wait_for_element_visible(button_selector, timeout=10)
                driver.click(button_selector)
            except Exception as e:
                print(f"{YELLOW}Erste Methode fehlgeschlagen: {str(e)}{RESET}")
                try:
                    button_xpath = '//*[@id="root"]/div[1]/div[2]/div[1]/div[2]/div[1]/div[2]/button[1]'
                    driver.wait_for_element_visible(button_xpath, timeout=10, by=By.XPATH)
                    driver.click(button_xpath, by=By.XPATH)
                    wait_for_user_or_timeout(10)
                except Exception as e:
                    print(f"{RED}Zweite Methode fehlgeschlagen: {str(e)}{RESET}")

            # Überprüfen Sie den Fehler bei der Kreditkartenverifizierung
            verification_failure_message = driver.find_elements(
                By.XPATH,
                '//div[@class="lrtcss-1qvxqj0" and contains(text(),"Kartenverifizierung fehlgeschlagen. Stellen Sie sicher, dass die Kartendaten korrekt sind.")]',
            )

            if verification_failure_message:
                print(f"{RED}Kartenverifizierung fehlgeschlagen. Erneut versuchen...{RESET}")
                wait_for_user_or_timeout(3)
                return False

            # Überprüfen Sie, ob eine Bestätigung erforderlich ist
            wait_for_user_or_timeout(10)
            confirmation_header1 = driver.find_elements(
                By.XPATH,
                '//h1[@class="confirmation-header centered" and text()="Bestätigung in C24 Bank App erforderlich"]'
            )
            confirmation_header2 = driver.find_elements(
                By.XPATH,
                '//p[text()="Wie möchten Sie diese Zahlung genehmigen?"]'
            )

            if confirmation_header1 or confirmation_header2:
                print(f"{YELLOW}Überprüfung erforderlich. Warten auf Benutzerbestätigung...{RESET}")
                print(f"{YELLOW}Warten auf Benutzeraktion oder Timeout...{RESET}")

                # Warten auf Benutzereingabe oder Timeout
                wait_for_user_or_timeout(120)

            else:
                print("Keine Bestätigung erkannt. Fortfahren 30 sec...")
                wait_for_user_or_timeout(30)

            # Fortfahren mit Eingabe des Sicherheitscodes oder Planbestätigung
            print("Suche nach Sicherheitscode-Eingabe...")
            try:
                security_code_input = driver.find_element(
                    By.XPATH,
                    '//input[@placeholder="Sicherheitscode eingeben"]'
                )
                if security_code_input:
                    print("Sicherheitscode eingeben...")
                    security_code_input.click()
                    security_code_input.send_keys(cvv)
                    security_code_input.send_keys(Keys.RETURN)
                else:
                    print(f"{YELLOW}Eingabe des Sicherheitscodes nicht gefunden. Fortfahren...{RESET}")
            except NoSuchElementException:
                print(f"{YELLOW}Eingabe des Sicherheitscodes nicht gefunden. Fortfahren...{RESET}")

            wait_for_user_or_timeout(10)

            # Überprüfen Sie den Erfolg der Planerstellung
            success_indicator_xpath = '//div[@class="lrtcss-morhn4" and text()="Plan erfolgreich erstellt!"]'
            success_elements = driver.find_elements(By.XPATH, success_indicator_xpath)

            if success_elements:
                print(f"{GREEN}Plan erfolgreich erstellt!{RESET}")
                success = True  # Beenden Sie die Schleife bei Erfolg
            else:
                print(f"{RED}Fehler beim Erstellen eines neuen Plans für den Betrag {fiat_amount}. Erneut versuchen...{RESET}")
                driver.refresh()  # Laden Sie die Seite neu, bevor Sie es erneut versuchen
                wait_for_user_or_timeout(3)

        except Exception as e:
            print(f"{RED}Ein Fehler ist aufgetreten: {str(e)}{RESET}")
            driver.save_screenshot("error_screenshot.png")
            driver.get_page_source()
            driver.refresh()  # Laden Sie die Seite neu, bevor Sie es erneut versuchen
            wait_for_user_or_timeout(3)

    return success

def main():
    """Hauptfunktion zur Ausführung der Automatisierungsaufgabe."""
    if not check_license():
        return  # Exit if the license is not valid

    extension_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "Extensions", "solver")
    )
    driver = None
    try:
        driver = initialize_driver(extension_path)
        if not driver:
            print(f"{RED}Treiberinitialisierung fehlgeschlagen. Beenden...{RESET}")
            return

        shared_secret = read_file("secret.txt")
        if shared_secret:
            print(f"Shared Secret: {shared_secret}")
        else:
            print(f"{YELLOW}Shared Secret fehlt. Fortfahren ohne TOTP...{RESET}")

        email, password = read_credentials("Credentials.txt")
        if not email or not password:
            print(f"{RED}Anmeldedaten fehlen oder sind ungültig. Beenden...{RESET}")
            return
        print(f"E-Mail: {email}")

        # Log in first
        if not login(driver, email, password, shared_secret):
            print(f"{RED}Anmeldung fehlgeschlagen. Beenden...{RESET}")
            return

        # Verwende nur eine Kreditkarte aus der Datei cc0.txt
        cc_file = "cc0.txt"
        cc_details = read_cc_details(cc_file)
        if not cc_details:
            print(
                f"{RED}Kreditkartendaten fehlen oder sind ungültig für {cc_file}. Beenden...{RESET}"
            )
            return

        (
            kreditkartennummer,
            datum,
            cvv,
            vorname,
            nachname,
            strasse,
            hausnummer,
            plz,
            stadt,
            land,
        ) = cc_details
        print(f"Verwenden der Kreditkartendatei: {cc_file}")

        # Fügen Sie die Kreditkarte nur einmal hinzu, wenn kein Plan vorhanden ist
        if not check_for_existing_plan(driver):
            print(f"{YELLOW}Kein bestehender Plan gefunden. Neue Karte hinzufügen...{RESET}")
            if not create_new_plan(
                    driver,
                    fiat_amount,
                    kreditkartennummer,
                    datum,
                    cvv,
                    vorname,
                    nachname,
                    strasse,
                    hausnummer,
                    plz,
                    stadt,
                    land,
            ):
                print(f"{RED}Fehler beim Hinzufügen der Kreditkarte. Beenden...{RESET}")
                return

        # Loop to perform three purchases
        for i in range(3):
            # Entferne vorhandene Pläne, falls vorhanden
            if check_for_existing_plan(driver):
                print(f"{YELLOW}Bestehender Plan gefunden. Plan wird entfernt...{RESET}")
                if not remove_plan(driver):
                    print(
                        f"{RED}Fehler beim Entfernen des bestehenden Plans. Fortfahren...{RESET}"
                    )
                    continue

            # Lese Fiat-Beträge aus summe.txt
            fiat_amounts = read_fiat_amounts("summe.txt")
            if not fiat_amounts:
                print(f"{RED}Keine Fiat-Beträge zu verarbeiten. Beenden...{RESET}")
                break  # Beenden Sie die Schleife, wenn keine Beträge mehr vorhanden sind

            # Verarbeiten Sie nur den ersten Betrag in der Liste
            fiat_amount = fiat_amounts[0]

            try:
                # Erstelle einen neuen Plan
                if not create_new_plan(
                        driver,
                        fiat_amount,
                        kreditkartennummer,
                        datum,
                        cvv,
                        vorname,
                        nachname,
                        strasse,
                        hausnummer,
                        plz,
                        stadt,
                        land,
                ):
                    print(
                        f"{RED}Fehler beim Erstellen eines neuen Plans für den Betrag {fiat_amount}. Erneut versuchen...{RESET}"
                    )
                    continue
                else:
                    print(
                        f"{GREEN}Erfolgreich einen neuen Plan für den Betrag {fiat_amount} erstellt.{RESET}"
                    )
                    remove_first_line("summe.txt")  # Entfernen Sie die erste Zeile nach erfolgreicher Verarbeitung

            except Exception as e:
                print(f"{RED}Ein Fehler ist aufgetreten: {str(e)}{RESET}")
                continue

    finally:
        if driver:
            driver.quit()
        print("Treiber geschlossen.")

if __name__ == "__main__":
    main()
