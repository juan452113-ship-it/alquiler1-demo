import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional

# ─── CLASES (adaptadas para Streamlit) ───────────────────────────────

class Vehiculo:
    def __init__(self, marca: str, modelo: str, matricula: str, tipo_motor: str):
        self.marca = marca
        self.modelo = modelo
        self.matricula = matricula
        self.tipo_motor = tipo_motor
        self.alquilado = False
        self.alquiler_actual = None  # referencia al alquiler

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.matricula}) - {self.tipo_motor}"

    def clave(self):
        return f"{self.marca} {self.modelo} | {self.matricula}"


class Cliente:
    def __init__(self, nombre: str, apellidos: str, domicilio: str, dni: str,
                 email: str, telefono: str, medio_pago: str):
        self.nombre = nombre
        self.apellidos = apellidos
        self.domicilio = domicilio
        self.dni = dni
        self.email = email
        self.telefono = telefono
        self.medio_pago = medio_pago

    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"


class Alquiler:
    def __init__(self, cliente: Cliente, vehiculo: Vehiculo, fecha_inicio: datetime, fecha_fin: datetime):
        self.cliente = cliente
        self.vehiculo = vehiculo
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin

    def duracion_dias(self) -> int:
        return (self.fecha_fin - self.fecha_inicio).days


class GestorAlquileres:
    def __init__(self):
        self.vehiculos = [
            Vehiculo("Renault", "Clio", "0001ABC", "Gasolina"),
            Vehiculo("Seat", "Ibiza", "0002BCD", "Gasolina"),
            Vehiculo("Volkswagen", "Golf", "0003CDE", "Híbrido"),
            Vehiculo("Toyota", "Corolla", "0004DEF", "Eléctrico")
        ]
        self.alquileres: List[Alquiler] = []

    def vehiculos_disponibles(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Vehiculo]:
        disp = []
        for v in self.vehiculos:
            if not v.alquilado:
                disp.append(v)
            else:
                alq = v.alquiler_actual
                if fecha_fin <= alq.fecha_inicio or fecha_inicio >= alq.fecha_fin:
                    disp.append(v)
        return disp

    def vehiculos_alquilados(self) -> List[Vehiculo]:
        return [v for v in self.vehiculos if v.alquilado]

    def registrar_alquiler(self, cliente: Cliente, matricula: str, fecha_inicio: datetime, fecha_fin: datetime) -> bool:
        vehiculo = next((v for v in self.vehiculos if v.matricula == matricula), None)
        if not vehiculo:
            return False
        if vehiculo not in self.vehiculos_disponibles(fecha_inicio, fecha_fin):
            return False
        alquiler = Alquiler(cliente, vehiculo, fecha_inicio, fecha_fin)
        self.alquileres.append(alquiler)
        vehiculo.alquilado = True
        vehiculo.alquiler_actual = alquiler
        return True

# ─── INICIALIZACIÓN EN SESSION STATE ───────────────────────────────

if "gestor" not in st.session_state:
    st.session_state.gestor = GestorAlquileres()

gestor = st.session_state.gestor

# ─── INTERFAZ STREAMLIT ────────────────────────────────────────────

st.set_page_config(
    page_title="🚗 Alquiler de Vehículos",
    page_icon="🚗",
    layout="centered"
)

st.title("🚗 Gestor de Alquiler de Vehículos")
st.markdown("Sistema para registrar y gestionar alquileres de 4 turismos.")

# ─── MENÚ LATERAL ──────────────────────────────────────────────────

menu = st.sidebar.radio("Menú", [
    "🆕 Registrar Alquiler",
    "🔍 Disponibilidad",
    "📋 Listados",
    "📄 Fichas"
])

# ─── 1. REGISTRAR ALQUILER ─────────────────────────────────────────

if menu == "🆕 Registrar Alquiler":
    st.header("🆕 Nuevo Alquiler")
    
    with st.form("form_alquiler"):
        st.subheader("Datos del cliente")
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre *", max_chars=50)
        apellidos = col2.text_input("Apellidos *", max_chars=80)
        dni = st.text_input("DNI/NIE *", max_chars=12, placeholder="Ej: 12345678Z")
        email = st.text_input("Email *", max_chars=100)
        telefono = st.text_input("Teléfono *", max_chars=15, placeholder="Ej: 600123456")
        domicilio = st.text_input("Domicilio *", max_chars=150)
        medio_pago = st.selectbox("Medio de pago", ["Tarjeta", "Transferencia", "Efectivo", "Otro"])
        
        st.subheader("Fechas y vehículo")
        col3, col4 = st.columns(2)
        fecha_inicio = col3.date_input("📅 Fecha de inicio", min_value=datetime.today().date())
        fecha_fin = col4.date_input("📅 Fecha de fin", min_value=fecha_inicio + timedelta(days=1))
        
        # Convertir a datetime (Streamlit devuelve date)
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.min.time())

        # Mostrar vehículos disponibles
        disponibles = gestor.vehiculos_disponibles(fecha_inicio_dt, fecha_fin_dt)
        if disponibles:
            opciones = {v.clave(): v.matricula for v in disponibles}
            vehiculo_sel = st.selectbox(
                "🚗 Selecciona un vehículo disponible",
                options=list(opciones.keys())
            )
        else:
            st.warning("⚠️ No hay vehículos disponibles en esas fechas.")
            vehiculo_sel = None

        submitted = st.form_submit_button("✅ Registrar Alquiler", type="primary")

    if submitted:
        errores = []
        if not nombre or not apellidos or not dni or not email or not telefono or not domicilio:
            errores.append("❌ Todos los campos con * son obligatorios.")
        if fecha_fin <= fecha_inicio:
            errores.append("❌ La fecha de fin debe ser posterior a la de inicio.")
        if not vehiculo_sel:
            errores.append("❌ Debes seleccionar un vehículo disponible.")

        if errores:
            for e in errores:
                st.error(e)
        else:
            matricula = opciones[vehiculo_sel]
            cliente = Cliente(nombre, apellidos, domicilio, dni, email, telefono, medio_pago)
            if gestor.registrar_alquiler(cliente, matricula, fecha_inicio_dt, fecha_fin_dt):
                st.success(f"✅ ¡Alquiler registrado con éxito!\n\n"
                          f"**{cliente.nombre_completo()}** alquiló **{vehiculo_sel}** del "
                          f"{fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}.")
            else:
                st.error("❌ Error al registrar el alquiler. Inténtelo de nuevo.")

# ─── 2. DISPONIBILIDAD ─────────────────────────────────────────────

elif menu == "🔍 Disponibilidad":
    st.header("🔍 Consultar disponibilidad")
    
    col1, col2 = st.columns(2)
    fi = col1.date_input("📅 Fecha de inicio", min_value=datetime.today().date(), key="disp_fi")
    ff = col2.date_input("📅 Fecha de fin", min_value=fi + timedelta(days=1), key="disp_ff")
    
    fi_dt = datetime.combine(fi, datetime.min.time())
    ff_dt = datetime.combine(ff, datetime.min.time())
    
    disp = gestor.vehiculos_disponibles(fi_dt, ff_dt)
    no_disp = [v for v in gestor.vehiculos if v not in disp]
    
    st.subheader(f"✅ Disponibles ({len(disp)}/{len(gestor.vehiculos)})")
    if disp:
        for v in disp:
            st.success(f"🟢 {v}")
    else:
        st.info("📌 Ningún vehículo disponible en ese rango.")
    
    st.subheader(f"🔒 Alquilados / No disponibles ({len(no_disp)})")
    for v in no_disp:
        alq = v.alquiler_actual
        if alq:
            info = f"Cliente: {alq.cliente.nombre_completo()} | {alq.fecha_inicio.strftime('%d/%m')} → {alq.fecha_fin.strftime('%d/%m')}"
        else:
            info = "No disponible (error interno)"
        st.error(f"🔴 {v} | {info}")

# ─── 3. LISTADOS ───────────────────────────────────────────────────

elif menu == "📋 Listados":
    st.header("📋 Listados")
    
    tab1, tab2, tab3 = st.tabs(["Vehículos", "Alquileres", "Resumen"])
    
    with tab1:
        st.subheader("Todos los vehículos")
        for v in gestor.vehiculos:
            estado = "🟢 Disponible" if not v.alquilado else "🔴 Alquilado"
            st.write(f"- **{v}** — {estado}")
    
    with tab2:
        st.subheader("Alquileres registrados")
        if not gestor.alquileres:
            st.info("📌 Aún no hay alquileres registrados.")
        else:
            for i, alq in enumerate(gestor.alquileres):
                dias = alq.duracion_dias()
                st.markdown(
                    f"**[{i+1}]** {alq.cliente.nombre_completo()} → "
                    f"{alq.vehiculo.marca} {alq.vehiculo.modelo} "
                    f"({alq.fecha_inicio.strftime('%d/%m/%Y')} - {alq.fecha_fin.strftime('%d/%m/%Y')}) — _{dias} días_"
                )
    
    with tab3:
        st.subheader("📊 Resumen")
        total = len(gestor.vehiculos)
        alq = len(gestor.vehiculos_alquilados())
        disp = total - alq
        st.metric("Vehículos totales", total)
        st.metric("Disponibles", disp, delta=f"+{disp}")
        st.metric("Alquilados", alq, delta=f"-{alq}")
        st.metric("Alquileres registrados", len(gestor.alquileres))

# ─── 4. FICHAS ─────────────────────────────────────────────────────

elif menu == "📄 Fichas":
    st.header("📄 Fichas de alquiler")
    
    if not gestor.alquileres:
        st.info("📌 No hay alquileres para mostrar.")
    else:
        seleccion = st.selectbox(
            "Selecciona un alquiler",
            options=[f"[{i+1}] {a.cliente.nombre_completo()} → {a.vehiculo.clave()}" 
                     for i, a in enumerate(gestor.alquileres)],
            key="ficha_sel"
        )
        
        idx = int(seleccion.split("]")[0].strip("["))
        alq = gestor.alquileres[idx]
        
        st.divider()
        st.subheader("📄 Ficha de Alquiler")
        st.markdown(f"""
        **Cliente**: {alq.cliente.nombre_completo()}  
        **DNI**: `{alq.cliente.dni}`  
        **Vehículo**: {alq.vehiculo.marca} {alq.vehiculo.modelo} (`{alq.vehiculo.matricula}`)  
        **Motor**: {alq.vehiculo.tipo_motor}  
        **Fechas**: {alq.fecha_inicio.strftime('%d/%m/%Y')} → {alq.fecha_fin.strftime('%d/%m/%Y')}  
        **Duración**: {alq.duracion_dias()} días  
        **Contacto**: 📞 `{alq.cliente.telefono}` | ✉️ `{alq.cliente.email}`  
        **Pago**: {alq.cliente.medio_pago}  
        **Domicilio**: {alq.cliente.domicilio}  
        """)
        st.divider()

# ─── PIE DE PÁGINA ─────────────────────────────────────────────────

st.sidebar.markdown("---")
st.sidebar.caption("✨ Demo ligera — Nov 2025")
st.sidebar.caption("Vehículos: Renault Clio, Seat Ibiza, VW Golf, Toyota Corolla")
