"""
Tests para las funciones de normalización financiera.
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal
from datetime import date

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.validators import normalize_amount, normalize_date


class TestNormalizeAmount:
    """Tests para normalize_amount() - Decimal-based financial normalization"""
    
    def test_us_format(self):
        """Formato US: $1,234.56"""
        assert normalize_amount("$1,234.56") == Decimal("1234.56")
        assert normalize_amount("1,234.56") == Decimal("1234.56")
        assert normalize_amount("$123.45") == Decimal("123.45")
    
    def test_european_format(self):
        """Formato europeo: 1.234,56"""
        assert normalize_amount("1.234,56") == Decimal("1234.56")
        assert normalize_amount("123,45") == Decimal("123.45")
    
    def test_panama_format(self):
        """Formato Panamá: B/. 1,234.56"""
        assert normalize_amount("B/. 1,234.56") == Decimal("1234.56")
        assert normalize_amount("B/.1234.56") == Decimal("1234.56")
        assert normalize_amount("B/ 59.95") == Decimal("59.95")
    
    def test_negative_parentheses(self):
        """Negativos entre paréntesis: (1,234.56)"""
        assert normalize_amount("(1,234.56)") == Decimal("-1234.56")
        assert normalize_amount("($500.00)") == Decimal("-500.00")
    
    def test_negative_sign(self):
        """Negativos con signo: -1234.56"""
        assert normalize_amount("-1234.56") == Decimal("-1234.56")
        assert normalize_amount("-$500.00") == Decimal("-500.00")
    
    def test_plain_numbers(self):
        """Números sin formato"""
        assert normalize_amount(1234.56) == Decimal("1234.56")
        assert normalize_amount(1234) == Decimal("1234.00")
        assert normalize_amount("1234.56") == Decimal("1234.56")
    
    def test_returns_decimal(self):
        """Siempre retorna Decimal (no float)"""
        result = normalize_amount("100.50")
        assert isinstance(result, Decimal)
    
    def test_invalid_returns_none(self):
        """Valores inválidos retornan None"""
        assert normalize_amount(None) is None
        assert normalize_amount("") is None
        assert normalize_amount("abc") is None
        assert normalize_amount("nan") is None


class TestNormalizeDate:
    """Tests para normalize_date() - Multi-format date normalization"""
    
    def test_dd_mm_yyyy(self):
        """Formato DD/MM/YYYY (Panamá)"""
        assert normalize_date("15/11/2025") == date(2025, 11, 15)
        assert normalize_date("01/12/2024") == date(2024, 12, 1)
    
    def test_yyyy_mm_dd(self):
        """Formato ISO: YYYY-MM-DD"""
        assert normalize_date("2025-11-15") == date(2025, 11, 15)
        assert normalize_date("2024-01-31") == date(2024, 1, 31)
    
    def test_dd_mm_yyyy_dash(self):
        """Formato DD-MM-YYYY"""
        assert normalize_date("15-11-2025") == date(2025, 11, 15)
    
    def test_european_dots(self):
        """Formato europeo: DD.MM.YYYY"""
        assert normalize_date("15.11.2025") == date(2025, 11, 15)
    
    def test_excel_serial(self):
        """Fechas seriales de Excel (número)"""
        # 45678 es aproximadamente 2025-01-13
        result = normalize_date(45678)
        assert result is not None
        assert isinstance(result, date)
        assert result.year == 2025
    
    def test_datetime_object(self):
        """Objetos datetime de Python"""
        from datetime import datetime
        dt = datetime(2025, 11, 15, 10, 30)
        assert normalize_date(dt) == date(2025, 11, 15)
    
    def test_weekday_prefix(self):
        """Fechas con prefijo de día: 'lun 15/11/2025'"""
        assert normalize_date("lun 15/11/2025") == date(2025, 11, 15)
        assert normalize_date("sáb 22/11/2025") == date(2025, 11, 22)
        assert normalize_date("mié 05/02/2025") == date(2025, 2, 5)
    
    def test_returns_date_object(self):
        """Siempre retorna date (no datetime ni string)"""
        result = normalize_date("15/11/2025")
        assert isinstance(result, date)
        assert not isinstance(result, type(None))
    
    def test_invalid_returns_none(self):
        """Valores inválidos retornan None"""
        assert normalize_date(None) is None
        assert normalize_date("") is None
        assert normalize_date("invalid") is None
        assert normalize_date("32/13/2025") is None  # Día/mes inválido


# Para ejecutar: pytest backend/tests/test_normalizers.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
