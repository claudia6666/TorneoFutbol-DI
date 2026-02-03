from PySide6.QtWidgets import QDialog, QTreeWidgetItem, QMessageBox, QDateEdit, QTimeEdit, QComboBox
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtSql import QSqlQuery
from PySide6.QtGui import QColor
from widgets.ui_calendaria import Ui_DialogCalendario
from views.form_partido import FormPartido
from models.globals import get_db_connection
class Calendario(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_DialogCalendario()
        self.ui.setupUi(self)
        self.partido_editando_id = None
        self.form_partido_window = FormPartido()
        self.ui.btnNuevoPartido.clicked.connect(self._abrir_formulario_nuevo)
        self.ui.btnEditarPartido.clicked.connect(self.editar_partido)
        self.ui.btnEliminarPartido.clicked.connect(self.eliminar_partido)
        self.ui.cmbEquipo1.currentIndexChanged.connect(self._aplicar_filtros)
        self.ui.cmbEquipo2.currentIndexChanged.connect(self._aplicar_filtros)
        self.ui.cmbArbitro.currentIndexChanged.connect(self._aplicar_filtros)
        self.ui.cmbEliminatoria.currentIndexChanged.connect(self._aplicar_filtros)
        self._configurar_tree()
        self._cargar_combos()
        self._cargar_partidos()
        try:
            self.ui.treePartidos.itemDoubleClicked.connect(lambda it, col: self.editar_partido())
        except Exception:
            pass
    def _configurar_tree(self):
        """Configura el aspecto del TreeWidget."""
        from PySide6.QtGui import QFont, QColor, QPalette
        self.ui.treePartidos.setColumnWidth(0, 400)
        self.ui.treePartidos.setColumnWidth(1, 250)
        self.ui.treePartidos.setColumnWidth(2, 250)
        self.ui.treePartidos.setSelectionMode(self.ui.treePartidos.SelectionMode.SingleSelection)
        font = QFont()
        font.setPointSize(9)
        font.setBold(False)
        self.ui.treePartidos.setFont(font)
        header = self.ui.treePartidos.header()
        if header:
            header_font = QFont()
            header_font.setPointSize(10)
            header_font.setBold(True)
            header.setFont(header_font)
            header_palette = header.palette()
            header_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            header_palette.setColor(QPalette.ColorRole.Button, QColor(1, 107, 97))
            header.setPalette(header_palette)
    def _cargar_combos(self):
        """Carga los datos en los ComboBoxes de filtros."""
        db = get_db_connection()
        self.ui.cmbEquipo1.clear()
        self.ui.cmbEquipo2.clear()
        self.ui.cmbEquipo1.addItem("Todos", None)
        self.ui.cmbEquipo2.addItem("Todos", None)
        query = QSqlQuery("SELECT id, nombre FROM equipos ORDER BY nombre", db)
        while query.next():
            equipo_id = query.value(0)
            nombre = query.value(1)
            self.ui.cmbEquipo1.addItem(nombre, equipo_id)
            self.ui.cmbEquipo2.addItem(nombre, equipo_id)
        self._actualizar_arbitros()
    def _actualizar_arbitros(self):
        """Actualiza solo la lista de árbitros sin disparar eventos de filtro."""
        db = get_db_connection()
        arbitro_actual = self.ui.cmbArbitro.currentData()
        try:
            self.ui.cmbArbitro.currentIndexChanged.disconnect(self._aplicar_filtros)
        except:
            pass
        self.ui.cmbArbitro.clear()
        self.ui.cmbArbitro.addItem("Todos", None)
        query = QSqlQuery(
            "SELECT id, nombre FROM participantes WHERE tipo_participante = 'Árbitro' ORDER BY nombre", 
            db
        )
        while query.next():
            arbitro_id = query.value(0)
            nombre = query.value(1)
            self.ui.cmbArbitro.addItem(nombre, arbitro_id)
        if arbitro_actual is not None:
            index = self.ui.cmbArbitro.findData(arbitro_actual)
            if index >= 0:
                self.ui.cmbArbitro.blockSignals(True)
                self.ui.cmbArbitro.setCurrentIndex(index)
                self.ui.cmbArbitro.blockSignals(False)
        self.ui.cmbArbitro.currentIndexChanged.connect(self._aplicar_filtros)
    def _abrir_formulario_nuevo(self):
        """Abre el formulario para crear un nuevo partido."""
        from views.form_partido import FormPartido
        form_partido = self.form_partido_window
        from PySide6.QtWidgets import QComboBox, QDateEdit, QTimeEdit, QPushButton
        def guardar_nuevo():
            try:
                db = get_db_connection()
                dialog = form_partido.dialog
                cmb_local = dialog.findChild(QComboBox, "cmbEquipoLocal")
                cmb_visitante = dialog.findChild(QComboBox, "cmbEquipoVisitante")
                cmb_arbitro = dialog.findChild(QComboBox, "cmbArbitro")
                cmb_eliminatoria = dialog.findChild(QComboBox, "cmbEliminatoria")
                date_fecha = dialog.findChild(QDateEdit, "dateFecha")
                time_hora = dialog.findChild(QTimeEdit, "timeHora")
                if cmb_local and cmb_visitante:
                    if cmb_local.currentData() == cmb_visitante.currentData():
                        QMessageBox.warning(dialog, "Validación", "Los equipos deben ser diferentes")
                        return
                query = QSqlQuery(db)
                query.prepare("""
                    INSERT INTO partidos (equipo1_id, equipo2_id, arbitro_id, goles_equipo1, goles_equipo2, fecha, hora, ronda, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Programado')
                """)
                query.addBindValue(cmb_local.currentData() if cmb_local else None)
                query.addBindValue(cmb_visitante.currentData() if cmb_visitante else None)
                query.addBindValue(cmb_arbitro.currentData() if cmb_arbitro else None)
                query.addBindValue(0)
                query.addBindValue(0)
                query.addBindValue(date_fecha.date().toString("yyyy-MM-dd") if date_fecha else "")
                query.addBindValue(time_hora.time().toString("HH:mm") if time_hora else "")
                query.addBindValue(cmb_eliminatoria.currentText() if cmb_eliminatoria else "Octavos")
                if query.exec():
                    QMessageBox.information(dialog, "Éxito", "Partido guardado correctamente")
                    dialog.close()
                else:
                    QMessageBox.critical(dialog, "Error", f"Error al guardar: {query.lastError().text()}")
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error inesperado: {str(e)}")
        form_partido._guardar_partido = guardar_nuevo
        buttons = form_partido.dialog.findChildren(QPushButton)
        for btn in buttons:
            if "Guardar" in btn.text() or "Save" in btn.text():
                try:
                    btn.clicked.disconnect()
                except:
                    pass
                btn.clicked.connect(guardar_nuevo)
        self._cargar_combos_formulario(form_partido.dialog)
        try:
            form_partido.dialog.finished.disconnect()
        except Exception:
            pass
        form_partido.dialog.finished.connect(self._actualizar_arbitros)
        form_partido.dialog.finished.connect(self._cargar_partidos)
        form_partido.show()
    def _cargar_combos_formulario(self, dialog):
        """Carga los ComboBoxes del formulario de partido."""
        db = get_db_connection()
        cmb_local = dialog.findChild(self.ui.cmbEquipo1.__class__, "cmbEquipoLocal")
        cmb_visitante = dialog.findChild(self.ui.cmbEquipo2.__class__, "cmbEquipoVisitante")
        cmb_arbitro = dialog.findChild(self.ui.cmbArbitro.__class__, "cmbArbitro")
        cmb_eliminatoria = dialog.findChild(self.ui.cmbEliminatoria.__class__, "cmbEliminatoria")
        if cmb_local:
            cmb_local.clear()
            query = QSqlQuery("SELECT id, nombre FROM equipos ORDER BY nombre", db)
            while query.next():
                cmb_local.addItem(query.value(1), query.value(0))
        if cmb_visitante:
            cmb_visitante.clear()
            query = QSqlQuery("SELECT id, nombre FROM equipos ORDER BY nombre", db)
            while query.next():
                cmb_visitante.addItem(query.value(1), query.value(0))
        if cmb_arbitro:
            cmb_arbitro.clear()
            cmb_arbitro.addItem("Sin asignar", None)
            query = QSqlQuery(
                "SELECT id, nombre FROM participantes WHERE tipo_participante = 'Árbitro' ORDER BY nombre",
                db
            )
            while query.next():
                cmb_arbitro.addItem(query.value(1), query.value(0))
        if cmb_eliminatoria:
            if cmb_eliminatoria.count() == 0:
                cmb_eliminatoria.addItems(["Todos", "Octavos", "Cuartos", "Semifinal", "Final"])
    def _cargar_partidos(self):
        """Carga los partidos en el TreeWidget aplicando filtros de los combos."""
        try:
            db = get_db_connection()
            self.ui.treePartidos.clear()
            equipo_filtro = self.ui.cmbEquipo1.currentData()
            equipo2_filtro = self.ui.cmbEquipo2.currentData()
            arbitro_filtro = self.ui.cmbArbitro.currentData()
            ronda_filtro = self.ui.cmbEliminatoria.currentText()
            query = QSqlQuery(db)
            query_str = """
                SELECT 
                    p.id,
                    COALESCE(e1.nombre, 'Equipo 1') AS equipo1,
                    COALESCE(e2.nombre, 'Equipo 2') AS equipo2,
                    p.fecha,
                    p.hora,
                    COALESCE(part.nombre, 'Sin asignar') AS arbitro,
                    COALESCE(p.ronda, '') AS ronda,
                    COALESCE(p.goles_equipo1, 0) AS goles1,
                    COALESCE(p.goles_equipo2, 0) AS goles2,
                    COALESCE(p.estado, 'Programado') AS estado
                FROM partidos p
                LEFT JOIN equipos e1 ON p.equipo1_id = e1.id
                LEFT JOIN equipos e2 ON p.equipo2_id = e2.id
                LEFT JOIN participantes part ON p.arbitro_id = part.id
                WHERE 1=1
            """
            if equipo_filtro is not None:
                query_str += f" AND (p.equipo1_id = {equipo_filtro} OR p.equipo2_id = {equipo_filtro})"
            if equipo2_filtro is not None:
                query_str += f" AND (p.equipo1_id = {equipo2_filtro} OR p.equipo2_id = {equipo2_filtro})"
            if arbitro_filtro is not None:
                query_str += f" AND p.arbitro_id = {arbitro_filtro}"
            if ronda_filtro and ronda_filtro != "Todos":
                query_str += f" AND p.ronda = '{ronda_filtro}'"
            query_str += " ORDER BY p.fecha DESC, p.hora DESC"
            print(f"[DEBUG] Query: {query_str}")
            if not query.exec(query_str):
                print(f"[ERROR] Error en query: {query.lastError().text()}")
                return
            row_count = 0
            while query.next():
                row_count += 1
                partido_id = query.value(0)
                equipo1 = query.value(1)
                equipo2 = query.value(2)
                fecha = query.value(3)
                hora = query.value(4)
                arbitro = query.value(5)
                ronda = query.value(6)
                goles1 = query.value(7)
                goles2 = query.value(8)
                estado = query.value(9)
                if estado == "Finalizado" and goles1 is not None and goles2 is not None:
                    partido_texto = f"{equipo1} {goles1} - {goles2} {equipo2}"
                else:
                    partido_texto = f"{equipo1} vs {equipo2}"
                if ronda:
                    partido_texto += f" ({ronda})"
                fecha_hora = f"{fecha} {hora}" if fecha and hora else fecha or ""
                item = QTreeWidgetItem([partido_texto, fecha_hora, arbitro])
                item.setData(0, Qt.UserRole, partido_id)
                if estado == "Finalizado":
                    item.setForeground(0, QColor(0, 100, 0))
                elif estado == "En curso":
                    item.setForeground(0, QColor(200, 100, 0))
                else:
                    item.setForeground(0, QColor(0, 0, 0))
                    item.setForeground(1, QColor(0, 0, 0))
                    item.setForeground(2, QColor(0, 0, 0))
                self.ui.treePartidos.addTopLevelItem(item)
            print(f"[DEBUG] Total partidos cargados: {row_count}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar partidos: {e}")
            import traceback
            traceback.print_exc()
    def _aplicar_filtros(self):
        """Recarga los partidos aplicando los filtros actuales (sin usar filtros por ahora)."""
        self._cargar_partidos()
    def editar_partido(self):
        """Edita el partido seleccionado."""
        item = self.ui.treePartidos.currentItem()
        if not item:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar un partido para editar.")
            return
        partido_id = item.data(0, Qt.UserRole)
        try:
            form_partido = self.form_partido_window
            self._cargar_combos_formulario(form_partido.dialog)
            db = get_db_connection()
            query = QSqlQuery(db)
            query.prepare("""
                SELECT equipo1_id, equipo2_id, arbitro_id, fecha, hora, ronda
                FROM partidos WHERE id = ?
            """)
            query.addBindValue(partido_id)
            if query.exec() and query.next():
                equipo1_id = query.value(0)
                equipo2_id = query.value(1)
                arbitro_id = query.value(2)
                fecha_str = query.value(3)
                hora_str = query.value(4)
                ronda = query.value(5)
                dialog = form_partido.dialog
                cmb_local = dialog.findChild(QComboBox, "cmbEquipoLocal")
                cmb_visitante = dialog.findChild(QComboBox, "cmbEquipoVisitante")
                cmb_arbitro = dialog.findChild(QComboBox, "cmbArbitro")
                cmb_eliminatoria = dialog.findChild(QComboBox, "cmbEliminatoria")
                date_fecha = dialog.findChild(QDateEdit, "dateFecha")
                time_hora = dialog.findChild(QTimeEdit, "timeHora")
                if cmb_local:
                    found = False
                    for i in range(cmb_local.count()):
                        if cmb_local.itemData(i) == equipo1_id:
                            cmb_local.setCurrentIndex(i)
                            found = True
                            break
                if cmb_visitante:
                    found = False
                    for i in range(cmb_visitante.count()):
                        if cmb_visitante.itemData(i) == equipo2_id:
                            cmb_visitante.setCurrentIndex(i)
                            found = True
                            break
                if cmb_arbitro and arbitro_id:
                    found = False
                    print(f"[DEBUG] Buscando arbitro_id {arbitro_id} en combo con {cmb_arbitro.count()} items")
                    for i in range(cmb_arbitro.count()):
                        item_data = cmb_arbitro.itemData(i)
                        item_text = cmb_arbitro.itemText(i)
                        print(f"[DEBUG]   Item {i}: text='{item_text}', data={item_data}")
                        if item_data == arbitro_id:
                            cmb_arbitro.setCurrentIndex(i)
                            found = True
                            print(f"[DEBUG] ¡Árbitro encontrado en índice {i}!")
                            break
                    if not found and arbitro_id:
                        print(f"[DEBUG] Árbitro ID {arbitro_id} no encontrado en combo")
                        cmb_arbitro.setCurrentIndex(0)
                elif cmb_arbitro and not arbitro_id:
                    print(f"[DEBUG] No hay árbitro asignado")
                    cmb_arbitro.setCurrentIndex(0)
                if cmb_eliminatoria and ronda:
                    for i in range(cmb_eliminatoria.count()):
                        if cmb_eliminatoria.itemText(i) == ronda:
                            cmb_eliminatoria.setCurrentIndex(i)
                            break
                if date_fecha and fecha_str:
                    fecha = QDate.fromString(fecha_str, "yyyy-MM-dd")
                    if fecha.isValid():
                        date_fecha.setDate(fecha)
                if time_hora and hora_str:
                    hora = QTime.fromString(hora_str, "HH:mm")
                    if hora.isValid():
                        time_hora.setTime(hora)
                self._modificar_guardado_para_edicion(form_partido, partido_id)
                try:
                    form_partido.dialog.finished.disconnect()
                except:
                    pass
                form_partido.dialog.finished.connect(self._actualizar_arbitros)
                form_partido.dialog.finished.connect(self._cargar_partidos)
                form_partido.show_for_edit()
            else:
                QMessageBox.warning(self, "Error", f"No se encontró el partido {partido_id}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al editar partido: {e}")
            import traceback
            traceback.print_exc()
    def _modificar_guardado_para_edicion(self, form_partido, partido_id):
        """Modifica el método de guardado para actualizar en vez de insertar."""
        from PySide6.QtWidgets import QComboBox, QDateEdit, QTimeEdit, QLineEdit, QTextEdit, QPushButton
        original_method = form_partido._guardar_partido
        def guardar_edicion():
            try:
                db = get_db_connection()
                dialog = form_partido.dialog
                cmb_local = dialog.findChild(QComboBox, "cmbEquipoLocal")
                cmb_visitante = dialog.findChild(QComboBox, "cmbEquipoVisitante")
                cmb_arbitro = dialog.findChild(QComboBox, "cmbArbitro")
                cmb_eliminatoria = dialog.findChild(QComboBox, "cmbEliminatoria")
                date_fecha = dialog.findChild(QDateEdit, "dateFecha")
                time_hora = dialog.findChild(QTimeEdit, "timeHora")
                if cmb_local and cmb_visitante:
                    if cmb_local.currentData() == cmb_visitante.currentData():
                        QMessageBox.warning(dialog, "Validación", "Los equipos deben ser diferentes")
                        return
                query = QSqlQuery(db)
                query.prepare("""
                    UPDATE partidos 
                    SET equipo1_id = ?, equipo2_id = ?, arbitro_id = ?, 
                        fecha = ?, hora = ?, ronda = ?
                    WHERE id = ?
                """)
                query.addBindValue(cmb_local.currentData() if cmb_local else None)
                query.addBindValue(cmb_visitante.currentData() if cmb_visitante else None)
                query.addBindValue(cmb_arbitro.currentData() if cmb_arbitro else None)
                query.addBindValue(date_fecha.date().toString("yyyy-MM-dd") if date_fecha else "")
                query.addBindValue(time_hora.time().toString("HH:mm") if time_hora else "")
                query.addBindValue(cmb_eliminatoria.currentText() if cmb_eliminatoria else "")
                query.addBindValue(partido_id)
                if query.exec():
                    QMessageBox.information(dialog, "Éxito", "Partido actualizado correctamente")
                    form_partido._guardar_partido = original_method
                    dialog.accept()
                else:
                    QMessageBox.critical(dialog, "Error", f"Error al actualizar: {query.lastError().text()}")
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error inesperado: {str(e)}")
        form_partido._guardar_partido = guardar_edicion
        buttons = form_partido.dialog.findChildren(QPushButton)
        for btn in buttons:
            if "Guardar" in btn.text() or "Save" in btn.text():
                try:
                    btn.clicked.disconnect()
                except:
                    pass
                btn.clicked.connect(guardar_edicion)
    def eliminar_partido(self):
        """Elimina el partido seleccionado."""
        item = self.ui.treePartidos.currentItem()
        if not item:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar un partido para eliminar.")
            return
        partido_id = item.data(0, Qt.UserRole)
        partido_texto = item.text(0)
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de eliminar el partido:\n\n{partido_texto}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            try:
                db = get_db_connection()
                query = QSqlQuery(db)
                query.prepare("DELETE FROM partidos WHERE id = ?")
                query.addBindValue(partido_id)
                if query.exec():
                    QMessageBox.information(self, "Éxito", "Partido eliminado correctamente.")
                    self._cargar_partidos()
                else:
                    QMessageBox.critical(
                        self, 
                        "Error", 
                        f"No se pudo eliminar el partido:\n{query.lastError().text()}"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar partido: {e}")
