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
            
            # Esperar a que se cargue la tabla de horarios
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "fondoVerde"))
            )
            
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