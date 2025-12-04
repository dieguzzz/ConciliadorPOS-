"""
Tests unitarios para las funciones de procesamiento bancario
"""

import pytest
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api_banco import detectar_tipo, extraer_codigo


class TestDetectarTipo:
    """Tests para la función detectar_tipo()"""
    
    def test_detectar_clave_con_pos(self):
        """Debe detectar CLAVE cuando la descripción contiene POS"""
        assert detectar_tipo("COMPRA POS 908068171") == "CLAVE"
        assert detectar_tipo("Transaccion POS Terminal 12345") == "CLAVE"
        assert detectar_tipo("pos 908068171 sucursal") == "CLAVE"
    
    def test_detectar_visa_con_tc(self):
        """Debe detectar VISA cuando la descripción contiene T/C"""
        assert detectar_tipo("COMPRA T/C 123456789") == "VISA"
        assert detectar_tipo("Pago TC VISA") == "VISA"
        assert detectar_tipo("TARJETA DE CREDITO") == "VISA"
    
    def test_detectar_otro(self):
        """Debe devolver OTRO para descripciones sin palabras clave"""
        assert detectar_tipo("Transferencia bancaria") == "OTRO"
        assert detectar_tipo("Deposito efectivo") == "OTRO"
        assert detectar_tipo("") == "OTRO"
    
    def test_detectar_tipo_none(self):
        """Debe manejar valores None o no-string"""
        assert detectar_tipo(None) == "OTRO"
        assert detectar_tipo(123) == "OTRO"
        assert detectar_tipo([]) == "OTRO"
    
    def test_detectar_tipo_case_insensitive(self):
        """Debe ser case-insensitive"""
        assert detectar_tipo("compra pos 123") == "CLAVE"
        assert detectar_tipo("COMPRA POS 123") == "CLAVE"
        assert detectar_tipo("Compra Pos 123") == "CLAVE"
        assert detectar_tipo("pago t/c visa") == "VISA"


class TestExtraerCodigo:
    """Tests para la función extraer_codigo()"""
    
    def test_extraer_codigo_basico(self):
        """Debe extraer código de 9 dígitos básico"""
        assert extraer_codigo("COMPRA POS 908068171") == "908068171"
        assert extraer_codigo("Terminal 123456789 sucursal") == "123456789"
    
    def test_extraer_codigo_con_palabra_clave(self):
        """Debe extraer código cuando está después de POS o TERMINAL"""
        assert extraer_codigo("TRANSACCION POS: 908068171") == "908068171"
        assert extraer_codigo("TERMINAL #123456789") == "123456789"
        assert extraer_codigo("POS 908068171 CONDADO") == "908068171"
    
    def test_extraer_codigo_con_guiones(self):
        """Debe extraer código con guiones o espacios"""
        assert extraer_codigo("POS 908-068-171") == "908068171"
        assert extraer_codigo("TERM 908 068 171") == "908068171"
        assert extraer_codigo("Terminal: 123-456-789") == "123456789"
    
    def test_extraer_codigo_multiples_numeros(self):
        """Debe tomar el último código si hay múltiples números de 9 dígitos"""
        desc = "Transaccion 111111111 POS 908068171"
        # Debería tomar 908068171 porque está después de POS
        assert extraer_codigo(desc) == "908068171"
    
    def test_extraer_codigo_sin_match(self):
        """Debe devolver None si no encuentra código válido"""
        assert extraer_codigo("Transferencia sin codigo") is None
        assert extraer_codigo("POS 12345") is None  # Solo 5 dígitos
        assert extraer_codigo("123") is None
    
    def test_extraer_codigo_none(self):
        """Debe manejar valores None o no-string"""
        assert extraer_codigo(None) is None
        assert extraer_codigo(123) is None
        assert extraer_codigo([]) is None
    
    def test_extraer_codigo_case_insensitive(self):
        """Debe funcionar con cualquier capitalización"""
        assert extraer_codigo("pos 908068171") == "908068171"
        assert extraer_codigo("POS 908068171") == "908068171"
        assert extraer_codigo("terminal 908068171") == "908068171"
        assert extraer_codigo("TERMINAL 908068171") == "908068171"
    
    def test_extraer_codigo_formato_real(self):
        """Debe funcionar con descripciones reales del banco"""
        # Ejemplos de descripciones reales
        desc1 = "COMPRA T/C VISA TERMINAL 908068171 BLACK DOG DELI"
        assert extraer_codigo(desc1) == "908068171"
        
        desc2 = "COMPRA POS CLAVE 123456789 CONDADO DEL REY"
        assert extraer_codigo(desc2) == "123456789"
        
        desc3 = "TRANSACCION POS: 908-068-171 SUCURSAL BELLA VISTA"
        assert extraer_codigo(desc3) == "908068171"


# Para ejecutar los tests:
# pytest backend/tests/test_banco_utils.py -v

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

