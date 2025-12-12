"""
API endpoints para exportar resultados a diferentes formatos.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import Dict, Any, List, Optional
import io
import pandas as pd
from datetime import datetime
from app.utils.logger import app_logger
from app.utils.response_formatter import success_response, error_response

router = APIRouter()


def create_excel_export(
    cierre_data: Optional[Dict[str, Any]] = None,
    yappy_data: Optional[Dict[str, Any]] = None,
    banco_data: Optional[Dict[str, Any]] = None,
    conciliacion_yappy: Optional[List[Dict[str, Any]]] = None,
    conciliacion_banco: Optional[List[Dict[str, Any]]] = None
) -> io.BytesIO:
    """
    Crea un archivo Excel con múltiples hojas.
    
    Args:
        cierre_data: Datos del cierre
        yappy_data: Datos de Yappy
        banco_data: Datos bancarios
        conciliacion_yappy: Resultados de conciliación Yappy
        conciliacion_banco: Resultados de conciliación Banco
    
    Returns:
        BytesIO con el archivo Excel
    """
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Resumen
            resumen_data = []
            if cierre_data:
                resumen_data.append(['Sucursal', cierre_data.get('meta', {}).get('sucursal', 'N/A')])
                resumen_data.append(['Fecha', cierre_data.get('meta', {}).get('fecha', 'N/A')])
                resumen_data.append(['Cajero', cierre_data.get('meta', {}).get('cajero', 'N/A')])
                resumen_data.append([])
                
                if cierre_data.get('totales'):
                    resumen_data.append(['TOTALES'])
                    for concepto, monto in cierre_data['totales'].items():
                        resumen_data.append([concepto, monto if monto is not None else 0])
            
            if resumen_data:
                df_resumen = pd.DataFrame(resumen_data)
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False, header=False)
            
            # Hoja 2: Conciliación Yappy
            if conciliacion_yappy and len(conciliacion_yappy) > 0:
                df_yappy = pd.DataFrame(conciliacion_yappy)
                df_yappy.to_excel(writer, sheet_name='Conciliación Yappy', index=False)
            
            # Hoja 3: Conciliación Banco
            if conciliacion_banco and len(conciliacion_banco) > 0:
                df_banco = pd.DataFrame(conciliacion_banco)
                df_banco.to_excel(writer, sheet_name='Conciliación Banco', index=False)
            
            # Hoja 4: Detalle Cierre
            if cierre_data and cierre_data.get('tabla'):
                df_detalle = pd.DataFrame(cierre_data['tabla'])
                df_detalle.to_excel(writer, sheet_name='Detalle Cierre', index=False)
            
            # Hoja 5: Detalle Yappy
            if cierre_data and cierre_data.get('detalle_yappy'):
                df_yappy_det = pd.DataFrame(cierre_data['detalle_yappy'])
                df_yappy_det.to_excel(writer, sheet_name='Detalle Yappy', index=False)
            
            # Hoja 6: Detalle Banco
            if banco_data and banco_data.get('preview'):
                df_banco_det = pd.DataFrame(banco_data['preview'])
                df_banco_det.to_excel(writer, sheet_name='Detalle Banco', index=False)
        
        output.seek(0)
        return output
        
    except Exception as e:
        app_logger.error(f"Error creando Excel: {str(e)}", exc_info=True)
        raise


@router.post("/export/excel")
async def export_to_excel(
    cierre_data: Optional[Dict[str, Any]] = None,
    yappy_data: Optional[Dict[str, Any]] = None,
    banco_data: Optional[Dict[str, Any]] = None,
    conciliacion_yappy: Optional[List[Dict[str, Any]]] = None,
    conciliacion_banco: Optional[List[Dict[str, Any]]] = None
):
    """
    Exporta los datos a Excel.
    
    Returns:
        Archivo Excel descargable
    """
    try:
        app_logger.info("Iniciando exportación a Excel")
        
        excel_file = create_excel_export(
            cierre_data=cierre_data,
            yappy_data=yappy_data,
            banco_data=banco_data,
            conciliacion_yappy=conciliacion_yappy,
            conciliacion_banco=conciliacion_banco
        )
        
        filename = f"conciliacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_file.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        app_logger.error(f"Error en exportación Excel: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al exportar a Excel: {str(e)}"
        )


@router.post("/export/csv")
async def export_to_csv(
    data: List[Dict[str, Any]],
    filename: Optional[str] = None
):
    """
    Exporta datos a CSV.
    
    Args:
        data: Lista de diccionarios con los datos
        filename: Nombre del archivo (opcional)
    
    Returns:
        Archivo CSV descargable
    """
    try:
        app_logger.info("Iniciando exportación a CSV")
        
        if not data or len(data) == 0:
            raise ValueError("No hay datos para exportar")
        
        df = pd.DataFrame(data)
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        app_logger.error(f"Error en exportación CSV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al exportar a CSV: {str(e)}"
        )

