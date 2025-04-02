from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv
import os
import time
import schedule
import logging
import platform
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Para mostrar en la terminal
        logging.FileHandler('booking_bot.log')  # Para guardar en un archivo
    ]
)

# Cargar variables de entorno
load_dotenv()

class RinconadaBookingBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.setup_driver()

    def setup_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)  # Aumentado a 20 segundos
            self.driver.maximize_window()
            self.logger.info("Driver configurado correctamente")
        except Exception as e:
            self.logger.error(f"Error al configurar el driver: {str(e)}")
            raise

    def accept_cookies(self):
        try:
            self.logger.info("Buscando botón de cookies...")
            # Intentar diferentes selectores para el botón de cookies
            selectors = [
                (By.ID, "onetrust-accept-btn-handler"),
                (By.XPATH, "//button[contains(text(), 'Aceptar')]"),
                (By.XPATH, "//button[contains(text(), 'Aceptar Cookies')]"),
                (By.XPATH, "//button[contains(text(), 'Aceptar todas')]"),
                (By.CLASS_NAME, "onetrust-accept-btn-handler")
            ]
            
            for by, selector in selectors:
                try:
                    self.logger.info(f"Intentando selector: {by} - {selector}")
                    cookie_button = self.wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    cookie_button.click()
                    self.logger.info("Cookies aceptadas")
                    time.sleep(2)  # Pequeña pausa después de aceptar cookies
                    return
                except Exception as e:
                    self.logger.info(f"Selector {selector} no funcionó: {str(e)}")
                    continue
            
            self.logger.info("No se encontró el botón de cookies, continuando...")
            
        except Exception as e:
            self.logger.error(f"Error al aceptar cookies: {str(e)}")
            # No lanzamos la excepción para continuar con el proceso

    def select_date_and_time(self):
        """Selects the date and time for the booking"""
        try:
            # Wait for the date input to be present
            date_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "se4"))
            )
            
            # Set the date using JavaScript with more robust event triggering
            self.driver.execute_script("""
                var dateInput = document.getElementById('se4');
                dateInput.value = '10/04/2024';
                
                // Trigger multiple events to ensure the datepicker updates
                ['change', 'input', 'blur'].forEach(function(eventType) {
                    var event = new Event(eventType, { bubbles: true });
                    dateInput.dispatchEvent(event);
                });
                
                // Force jQuery datepicker to update if it exists
                if (jQuery && jQuery.datepicker) {
                    jQuery('#se4').datepicker('setDate', '10/04/2024');
                }
            """)
            
            # Wait a moment for the datepicker to update
            time.sleep(3)
            
            # Get the current value to verify
            current_value = self.driver.execute_script("return document.getElementById('se4').value;")
            logging.info(f"Date input value after setting: {current_value}")
            
            # Wait for the search button and make sure it's visible
            search_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "botonbuscar"))
            )
            
            # Scroll the button into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(2)
            
            # Click using JavaScript to ensure the click happens
            self.driver.execute_script("arguments[0].click();", search_button)
            
            # Wait longer for the schedule table to update
            time.sleep(5)
            
            # Save the HTML of the page for analysis
            with open("horarios_page.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            # Find available time slots
            available_slots = self.driver.find_elements(By.CLASS_NAME, "fondoVerde")
            logging.info(f"Found {len(available_slots)} available time slots")
            
            return True
            
        except Exception as e:
            logging.error(f"Error selecting date and time: {str(e)}")
            return False

    def select_time_and_book(self):
        """Select an available time slot and click the reserve button"""
        try:
            # Wait for the schedule table to load
            table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table"))
            )
            
            # Wait for available slots and get them
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "fondoVerde"))
            )
            available_slots = self.driver.find_elements(By.CLASS_NAME, "fondoVerde")
            logging.info(f"Found {len(available_slots)} available time slots")
            
            if not available_slots:
                logging.error("No available time slots found")
                return False
            
            # Get all slot times for logging
            for slot in available_slots:
                slot_text = slot.text if slot.text else "No text"
                slot_id = slot.get_attribute("id") if slot.get_attribute("id") else "No ID"
                logging.info(f"Available slot - Text: {slot_text}, ID: {slot_id}")
            
            # Select the first available slot
            time_slot = available_slots[0]
            
            # Scroll to the time slot
            self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", time_slot)
            time.sleep(3)  # Wait for scroll to complete
            
            # Try to click using different methods
            try:
                # First try: Direct click
                time_slot.click()
            except Exception as e1:
                logging.info(f"Direct click failed: {str(e1)}, trying JavaScript click")
                try:
                    # Second try: JavaScript click
                    self.driver.execute_script("arguments[0].click();", time_slot)
                except Exception as e2:
                    logging.info(f"JavaScript click failed: {str(e2)}, trying Actions chain")
                    # Third try: Actions chain
                    actions = ActionChains(self.driver)
                    actions.move_to_element(time_slot).click().perform()
            
            time.sleep(2)  # Wait after clicking
            
            # Wait for and find the reserve button
            try:
                reserve_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "botonreservar"))
                )
                
                # Scroll to the reserve button
                self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", reserve_button)
                time.sleep(2)
                
                # Try to click the reserve button using different methods
                try:
                    # First try: Direct click
                    reserve_button.click()
                except Exception as e1:
                    logging.info(f"Direct click on reserve failed: {str(e1)}, trying JavaScript")
                    try:
                        # Second try: JavaScript click
                        self.driver.execute_script("arguments[0].click();", reserve_button)
                    except Exception as e2:
                        logging.info(f"JavaScript click on reserve failed: {str(e2)}, trying Actions")
                        # Third try: Actions chain
                        actions = ActionChains(self.driver)
                        actions.move_to_element(reserve_button).click().perform()
                
                logging.info("Successfully clicked reserve button")
                return True
                
            except Exception as e:
                logging.error(f"Error with reserve button: {str(e)}")
                return False
            
        except Exception as e:
            logging.error(f"Error selecting time and booking: {str(e)}")
            return False

    def navigate_to_booking(self):
        """Navega al menú de alquileres y selecciona la actividad e instalación"""
        try:
            # Navegar a la página de alquileres
            self.logger.info("Navegando al menú de alquileres...")
            self.driver.get("https://online.pmdlarinconada.es/deportes/alqInst.php?alq=1")
            time.sleep(3)  # Esperar a que la página cargue
            
            # Esperar a que se cargue el selector de actividad
            actividad_select = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "se1"))
            )
            
            # Hacer scroll hasta el elemento
            self.driver.execute_script("arguments[0].scrollIntoView(true);", actividad_select)
            time.sleep(1)  # Esperar a que el scroll termine
            
            # Seleccionar la actividad "FUTBOL-7/11/RUGBY"
            self.logger.info("Seleccionando actividad FUTBOL-7/11/RUGBY...")
            Select(actividad_select).select_by_value("011")
            time.sleep(2)  # Esperar a que se actualice el selector de complejos
            
            # Esperar a que se cargue el selector de complejos
            complejo_select = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "se2"))
            )
            
            # Hacer scroll hasta el elemento
            self.driver.execute_script("arguments[0].scrollIntoView(true);", complejo_select)
            time.sleep(1)  # Esperar a que el scroll termine
            
            # Seleccionar el complejo "El Santísimo"
            self.logger.info("Seleccionando complejo El Santísimo...")
            Select(complejo_select).select_by_value("005")
            time.sleep(2)  # Esperar a que se actualice el selector de instalaciones
            
            # Esperar a que se cargue el selector de instalaciones
            instalacion_select = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "se3"))
            )
            
            # Hacer scroll hasta el elemento
            self.driver.execute_script("arguments[0].scrollIntoView(true);", instalacion_select)
            time.sleep(1)  # Esperar a que el scroll termine
            
            # Seleccionar la instalación "Pol. El Santísimo"
            self.logger.info("Seleccionando instalación Pol. El Santísimo...")
            Select(instalacion_select).select_by_value("05110100")  # FUTBOL 7 ARTIFICIAL
            time.sleep(2)  # Esperar a que se cargue la tabla de horarios
            
            # Seleccionar la fecha
            self.select_date_and_time()
            
            # Seleccionar la hora y hacer la reserva
            self.select_time_and_book()
            
            self.logger.info("Navegación completada correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la navegación: {str(e)}")
            return False

    def login(self):
        try:
            self.logger.info("Iniciando sesión...")
            # Ir directamente a la página de login
            self.driver.get("https://online.pmdlarinconada.es/deportes/zonaabo.php")
            time.sleep(5)  # Esperar a que la página cargue completamente
            
            # Hacer clic en el botón de aceptar cookies
            try:
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "gdpr-cookie-accept"))
                )
                cookie_button.click()
                self.logger.info("Cookies aceptadas")
                time.sleep(2)  # Esperar a que se cierre el diálogo de cookies
            except Exception as e:
                self.logger.info("No se encontró el botón de cookies o ya estaba cerrado")
            
            # Aquí implementaremos el login con las credenciales
            username = os.getenv("RINCONADA_USERNAME")
            password = os.getenv("RINCONADA_PASSWORD")
            
            if not username or not password:
                raise ValueError("Las credenciales no están configuradas en el archivo .env")
            
            # Esperar a que aparezcan los campos de login
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "usuario"))
            )
            password_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            
            # Rellenar los campos
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Hacer clic en el botón de login
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "validar"))
            )
            login_button.click()
            self.logger.info("Login completado")
            time.sleep(3)  # Esperar a que se complete el login
            
            self.navigate_to_booking()
            
        except Exception as e:
            self.logger.error(f"Error durante el login: {str(e)}")
            raise

    def book_field(self, date, time_slot):
        try:
            self.logger.info(f"Intentando reservar para {date} a las {time_slot}")
        except Exception as e:
            self.logger.error(f"Error durante la reserva: {str(e)}")
            raise

    def __del__(self):
        if self.driver:
            self.driver.quit()

def main():
    try:
        bot = RinconadaBookingBot()
        bot.login()
    except Exception as e:
        logging.error(f"Error en el proceso principal: {str(e)}")

if __name__ == "__main__":
    main() 