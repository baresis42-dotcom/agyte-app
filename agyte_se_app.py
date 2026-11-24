import streamlit as st
from datetime import datetime
import time
import random
from streamlit.components.v1 import html
import psycopg2
from psycopg2.extras import RealDictCursor
import os

def formatar_cpf(cpf):
    if not cpf:
        return ""
    return ''.join(filter(str.isdigit, cpf))

def formatar_telefone(telefone):
    if not telefone:
        return ""
    return ''.join(filter(str.isdigit, telefone))

def get_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets.get("DB_HOST"),
            database=st.secrets.get("DB_NAME"),
            user=st.secrets.get("DB_USER"),
            password=st.secrets.get("DB_PASSWORD"),
            port=int(st.secrets.get("DB_PORT", 5432)),
            connect_timeout=3
        )
        return conn
    except:
        return None

def inserir_participante(nome, cpf, setor, unidade, telefone, numero_vip, evento="FUNCIONAL"):
    try:
        conn = get_connection()
        if conn is None:
            return True, "⚠️ Participante não salvo (banco inacessível), mas dados foram preenchidos."
        cur = conn.cursor()
        sql = """
            INSERT INTO public.agyte_participantes
                (nome, cpf, setor, unidade, telefone, numero_vip, evento)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, (nome.upper(), cpf, setor if setor else "Não informado", unidade, telefone, numero_vip, evento))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Participante cadastrado com sucesso!"
    except psycopg2.IntegrityError as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, "CPF já cadastrado!"
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, str(e)

def contar_participantes():
    try:
        conn = get_connection()
        if conn is None:
            return 0
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM public.agyte_participantes WHERE evento = 'FUNCIONAL'")
        resultado = cur.fetchone()
        total = resultado[0] if resultado else 0
        cur.close()
        conn.close()
        return total
    except Exception as e:
        return 0

def verificar_cpf_existente(cpf):
    try:
        conn = get_connection()
        if conn is None:
            return False
        cur = conn.cursor()
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        cur.execute("""
            SELECT COUNT(*) FROM public.agyte_participantes 
            WHERE evento = 'FUNCIONAL' 
            AND REPLACE(REPLACE(cpf, '.', ''), '-', '') = %s
        """, (cpf_limpo,))
        resultado = cur.fetchone()
        existe = resultado[0] > 0 if resultado else False
        cur.close()
        conn.close()
        return existe
    except Exception as e:
        return False

def obter_proximo_numero():
    try:
        conn = get_connection()
        if conn is None:
            return 1
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(MAX(numero_vip), 0) as ultimo_numero 
            FROM public.agyte_participantes 
            WHERE evento = 'FUNCIONAL'
        """)
        resultado = cur.fetchone()
        ultimo_numero = resultado[0] if resultado else 0
        cur.close()
        conn.close()
        return ultimo_numero + 1
    except Exception as e:
        return 1

st.set_page_config(
    page_title="AULÃO FUNCIONAL",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 15%, #fbcfe8 30%, #f9a8d4 50%, #fbcfe8 70%, #fce7f3 85%, #fdf2f8 100%);
        background-size: 400% 400%;
        animation: fluidGradient 12s ease infinite;
        min-height: 100vh;
    }
    @keyframes fluidGradient {
        0% { background-position: 0% 50%; }
        25% { background-position: 50% 100%; }
        50% { background-position: 100% 50%; }
        75% { background-position: 50% 0%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes breathe { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.03); } }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.04); } }
    @keyframes glowPulse { 0%, 100% { box-shadow: 0 0 40px rgba(219, 39, 119, 0.5); } 50% { box-shadow: 0 0 80px rgba(244, 114, 182, 0.8); } }
    @keyframes badgeFloat { 0%, 100% { transform: translateY(0) scale(1); } 50% { transform: translateY(-10px) scale(1.03); } }
    @keyframes iconFloat { 0%, 100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-18px) rotate(5deg); } }
    @keyframes vipPulse { 0% { transform: scale(1); text-shadow: 0 0 30px rgba(255, 255, 255, 0.8); } 100% { transform: scale(1.06); text-shadow: 0 0 60px rgba(255, 255, 255, 1); } }
    
    .main-container {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(30px);
        border-radius: 40px;
        border: 2px solid rgba(244, 114, 182, 0.5);
        box-shadow: 0 25px 70px rgba(0, 0, 0, 0.1), 0 0 100px rgba(219, 39, 119, 0.25), inset 0 0 60px rgba(255, 255, 255, 0.6);
        padding: 3rem 2rem;
        margin: 1rem;
        position: relative;
        z-index: 10;
    }
    
    .circle-header {
        width: 220px;
        height: 220px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f472b6 0%, #ec4899 30%, #db2777 70%, #be185d 100%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 1.5rem;
        box-shadow: 0 10px 35px rgba(219, 39, 119, 0.4), 0 0 80px rgba(244, 114, 182, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.4);
        border: 4px solid rgba(255, 255, 255, 0.8);
        margin: 0 auto;
        animation: breathe 5s infinite ease-in-out, glowPulse 3s infinite alternate;
    }
    
    .circle-header .programa { font-size: 0.95rem; font-weight: 800; color: white; text-transform: uppercase; letter-spacing: 4px; margin-bottom: 0.3rem; text-shadow: 0 0 15px rgba(255, 255, 255, 0.8); }
    .circle-header .title { font-size: clamp(1.5rem, 5vw, 2rem); font-weight: 900; color: white; margin: 0.2rem 0; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 25px rgba(255, 255, 255, 1); line-height: 1.1; }
    .circle-header .subtitle { font-size: 0.85rem; font-weight: 700; color: rgba(255, 255, 255, 0.95); letter-spacing: 3px; margin-top: 0.3rem; }
    
    .event-badge {
        display: inline-block;
        background: linear-gradient(45deg, rgba(219, 39, 119, 0.9), rgba(244, 114, 182, 0.8));
        color: white;
        padding: 1.2rem 3rem;
        border-radius: 50px;
        font-weight: 900;
        letter-spacing: 3px;
        margin-top: 1.5rem;
        text-transform: uppercase;
        font-size: 1.15rem;
        border: 3px solid rgba(255, 255, 255, 0.7);
        box-shadow: 0 0 60px rgba(219, 39, 119, 0.7), 0 20px 50px rgba(0, 0, 0, 0.12);
        animation: badgeFloat 4s infinite ease-in-out;
    }
    
    .form-container {
        background: rgba(255, 255, 255, 0.85);
        border-radius: 30px;
        padding: 3rem;
        margin: 2rem auto;
        max-width: 800px;
        border: 2px solid rgba(244, 114, 182, 0.5);
        box-shadow: 0 25px 70px rgba(0, 0, 0, 0.08), 0 0 100px rgba(219, 39, 119, 0.3);
    }
    
    .form-title { color: #be185d; font-size: 2.5rem; text-align: center; margin-bottom: 1.5rem; font-weight: 900; text-transform: uppercase; letter-spacing: 3px; text-shadow: 0 0 30px rgba(219, 39, 119, 0.5); }
    
    .stTextInput > div > div > input, .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid rgba(244, 114, 182, 0.6) !important;
        border-radius: 15px !important;
        padding: 1.2rem !important;
        font-size: 1.2rem !important;
        color: #831843 !important;
        box-shadow: inset 0 0 25px rgba(219, 39, 119, 0.1), 0 0 25px rgba(219, 39, 119, 0.2) !important;
    }
    
    .stTextInput label, .stSelectbox label { color: #be185d !important; font-weight: 800 !important; font-size: 1.1rem !important; text-transform: uppercase !important; }
    
    .stButton button {
        background: linear-gradient(45deg, #be185d 0%, #db2777 30%, #f472b6 50%, #db2777 70%, #be185d 100%) !important;
        background-size: 300% 100% !important;
        color: white !important;
        border: 4px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: 25px !important;
        padding: 1.8rem 3rem !important;
        font-size: 1.8rem !important;
        font-weight: 900 !important;
        letter-spacing: 3px !important;
        width: 100% !important;
        margin-top: 2rem !important;
        box-shadow: 0 0 80px rgba(219, 39, 119, 0.8) !important;
        animation: breathe 3s infinite ease-in-out, buttonShine 4s infinite;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    @media (max-width: 768px) {
        .main-container { padding: 1.5rem !important; }
        .circle-header { width: 180px !important; height: 180px !important; }
        .form-container { padding: 1.5rem !important; }
        .form-title { font-size: 1.8rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# CONTEÚDO PRINCIPAL (HTML COMPACTADO PARA NÃO QUEBRAR)
st.markdown("""
<div class="main-container">
    <div class="circle-header">
        <div class="programa">CONFRA</div>
        <div class="title">AULÃO</div>
        <div class="subtitle">💪 FUNCIONAL 💪</div>
    </div>
    <div style="text-align: center;">
        <div class="event-badge">💪 VAMOS CONTINUAR O MOVIMENTO! 💪</div>
    </div>
    <div style="margin-top: 2rem; color: #be185d; font-size: 1.3rem; font-weight: 700; text-align: center;">
        Prepare-se para o Aulão Funcional! Um momento de energia, saúde e movimento na praia.
    </div>
</div>
""", unsafe_allow_html=True)

# DETALHES DO EVENTO (HTML COMPACTADO)
st.markdown("""
<div style='text-align: center; margin: 3rem 0;'>
    <div style='background: rgba(255, 255, 255, 0.75); border-radius: 25px; padding: 2rem; border: 2px solid rgba(244, 114, 182, 0.5); backdrop-filter: blur(15px); box-shadow: 0 0 60px rgba(219, 39, 119, 0.3);'>
        <h2 style='color: #be185d; margin-bottom: 1.5rem; font-size: 2.2rem; text-shadow: 0 0 20px rgba(219, 39, 119, 0.4);'>💪 DETALHES DO EVENTO</h2>
        <div style='color: #831843; font-size: 1.2rem; line-height: 1.6; padding: 0 1rem;'>
            <div style='margin-bottom: 1rem;'>📅 <span style='color: #db2777; font-weight: 700;'>Data:</span> 05 de Dezembro</div>
            <div style='margin-bottom: 1rem;'>⏰ <span style='color: #db2777; font-weight: 700;'>Horário:</span> 05:45</div>
            <div style='margin-bottom: 1rem;'>📍 <span style='color: #db2777; font-weight: 700;'>Local:</span> Faixa de Areia Beira Mar (Em frente ao Hotel Bourbon)</div>
            <div style='margin-bottom: 1rem;'>📌 <span style='color: #db2777; font-weight: 700;'>Endereço:</span> Av. Beira Mar, nº 2340 - Meireles, Fortaleza - CE</div>
            <div style='margin-bottom: 1.5rem;'>💰 <span style='color: #db2777; font-weight: 900;'>Taxa Social:</span> R$ 10,00 (Revertida para instituições carentes)</div>
            <div style='margin-top: 1rem; color: #db2777; font-weight: 800; font-size: 1.3rem;'>⏰ <span style='background: rgba(219, 39, 119, 0.2); padding: 3px 12px; border-radius: 8px;'>INSCRIÇÕES: 25/11/2026 às 12:00</span></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

total_banco_atual = contar_participantes()
proximo_numero_atual = obter_proximo_numero()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style='background: rgba(255, 255, 255, 0.8); border-radius: 25px; padding: 2rem; text-align: center; border: 2px solid rgba(244, 114, 182, 0.5); backdrop-filter: blur(10px); box-shadow: 0 0 40px rgba(219, 39, 119, 0.3); height: 100%;'>
        <div style='font-size: 4rem; font-weight: 900; color: #be185d; text-shadow: 0 0 30px rgba(219, 39, 119, 0.5); margin-bottom: 0.8rem;'>{total_banco_atual}/50</div>
        <div style='color: #db2777; font-size: 1.2rem; text-transform: uppercase; letter-spacing: 3px; font-weight: 700;'>INSCRITOS</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: rgba(255, 255, 255, 0.8); border-radius: 25px; padding: 2rem; text-align: center; border: 2px solid rgba(244, 114, 182, 0.5); backdrop-filter: blur(10px); box-shadow: 0 0 40px rgba(219, 39, 119, 0.3); height: 100%;'>
        <div style='font-size: 3rem; color: #be185d; margin-bottom: 1rem;'>💪</div>
        <div style='font-size: 1.2rem; color: #831843; font-weight: 900; margin-bottom: 0.5rem; line-height: 1.6;'>AULÃO<br>FUNCIONAL</div>
        <div style='color: #db2777; font-size: 1.5rem; font-weight: 700;'>50 VAGAS</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='background: rgba(255, 255, 255, 0.8); border-radius: 25px; padding: 2rem; text-align: center; border: 2px solid rgba(244, 114, 182, 0.5); backdrop-filter: blur(10px); box-shadow: 0 0 40px rgba(219, 39, 119, 0.3); height: 100%;'>
        <div style='font-size: 3rem; color: #be185d; margin-bottom: 1rem;'>📍</div>
        <div style='font-size: 1.1rem; color: #831843; font-weight: 900; margin-bottom: 0.5rem; line-height: 1.4;'>Beira Mar<br>Meireles</div>
        <div style='color: #db2777; font-size: 1.2rem; font-weight: 700;'>05/DEZ • 05:45</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="form-container">
    <h2 class="form-title">💪 GARANTA SUA VAGA NO AULÃO!</h2>
    <div style='color: #be185d; text-align: center; margin-bottom: 3rem; font-weight: 700; letter-spacing: 2px; font-size: 1.2rem;'>CADA FUNCIONÁRIO PODE LEVAR 1 DEPENDENTE</div>
""", unsafe_allow_html=True)

if 'mostrar_caixa_sucesso' not in st.session_state:
    st.session_state.mostrar_caixa_sucesso = False
if 'numero_vip_sucesso' not in st.session_state:
    st.session_state.numero_vip_sucesso = 0
if 'mostrar_caixa_erro' not in st.session_state:
    st.session_state.mostrar_caixa_erro = False
if 'mensagem_erro' not in st.session_state:
    st.session_state.mensagem_erro = ""

with st.form("cadastro_premium"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("NOME COMPLETO *", placeholder="DIGITE SEU NOME")
    with col2:
        cpf_input = st.text_input("CPF *", placeholder="000.000.000-00", max_chars=14)
    
    setor = st.text_input("SETOR DE ATUAÇÃO", placeholder="Ex: TI, Comercial... (opcional)")
    unidade = st.selectbox("UNIDADE *", ["🏢 DILADY", "💖 FINNA", "❤️ LOVE"])
    telefone_input = st.text_input("WHATSAPP *", placeholder="(85) 99999-9999", max_chars=15)
    
    if st.session_state.mostrar_caixa_sucesso:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(219, 39, 119, 0.95) 0%, rgba(244, 114, 182, 0.95) 100%); border-radius: 20px; padding: 2rem; margin: 2rem 0; border: 3px solid rgba(255, 255, 255, 0.9); box-shadow: 0 0 60px rgba(219, 39, 119, 0.8); text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>💪</div>
            <div style='font-size: 2.2rem; font-weight: 900; color: #ffffff; margin-bottom: 1rem;'>✅ INSCRIÇÃO CONFIRMADA!</div>
            <div style='font-size: 4rem; font-weight: 900; color: #ffffff; margin: 1rem 0; animation: vipPulse 2s infinite alternate;'>Nº {st.session_state.numero_vip_sucesso}</div>
            <div style='font-size: 1.5rem; color: #ffffff; font-weight: 700;'>VAGA GARANTIDA NO AULÃO FUNCIONAL! 💪</div>
            <div style='font-size: 1.1rem; color: #ffffff; margin-top: 0.5rem;'>05/DEZ • 05:45 • Beira Mar</div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.mostrar_caixa_erro:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(220, 38, 38, 0.95) 0%, rgba(239, 68, 68, 0.95) 100%); border-radius: 20px; padding: 2rem; margin: 2rem 0; border: 3px solid rgba(255, 255, 255, 0.9); box-shadow: 0 0 60px rgba(239, 68, 68, 0.8); text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>⚠️</div>
            <div style='font-size: 2rem; font-weight: 900; color: #ffffff; margin-bottom: 1rem;'>ATENÇÃO!</div>
            <div style='font-size: 1.6rem; color: #ffffff; font-weight: 700;'>{st.session_state.mensagem_erro}</div>
        </div>
        """, unsafe_allow_html=True)
    
    submitted = st.form_submit_button("💪 CLIQUE AQUI PRA GARANTIR SUA VAGA! 💪", use_container_width=True)

st.markdown("""
<div style="text-align: center; margin: 1.5rem 0; padding: 1.2rem; background: rgba(244, 114, 182, 0.25); border-radius: 15px; border: 3px dashed rgba(219, 39, 119, 0.5);">
    <div style="color: #be185d; font-size: 1.3rem; font-weight: 900; margin-bottom: 0.8rem; text-transform: uppercase;">⚡ PREENCHA TODOS OS CAMPOS ACIMA ⚡</div>
    <div style="color: #831843; font-size: 1.1rem; font-weight: 700;">E CLIQUE NO BOTÃO ROSA PARA FINALIZAR!</div>
</div>
</div>
""", unsafe_allow_html=True)

if submitted:
    st.session_state.mostrar_caixa_sucesso = False
    st.session_state.mostrar_caixa_erro = False
    
    total_banco_atual = contar_participantes()
    proximo_numero_atual = obter_proximo_numero()
    
    nome_limpo = nome.strip().upper() if nome else ""
    cpf_limpo = formatar_cpf(cpf_input)
    telefone_limpo = formatar_telefone(telefone_input)
    setor_limpo = setor.strip() if setor else ""
    
    if not nome_limpo or not cpf_limpo or not telefone_limpo:
        st.session_state.mensagem_erro = "Preencha todos os campos obrigatórios (*)!"
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    elif len(cpf_limpo) != 11:
        st.session_state.mensagem_erro = f"CPF deve ter 11 números! Você digitou {len(cpf_limpo)}."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    elif len(telefone_limpo) < 10:
        st.session_state.mensagem_erro = f"Telefone deve ter pelo menos 10 números! Você digitou {len(telefone_limpo)}."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    elif total_banco_atual >= 50:
        st.session_state.mensagem_erro = "VAGAS ESGOTADAS! Todas as 50 vagas já foram preenchidas."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    elif verificar_cpf_existente(cpf_limpo):
        st.session_state.mensagem_erro = "Este CPF já está cadastrado no AULÃO FUNCIONAL!"
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    else:
        unidade_formatada = unidade.replace("🏢", "").replace("💖", "").replace("❤️", "").strip()
        success, message = inserir_participante(nome=nome_limpo, cpf=cpf_limpo, setor=setor_limpo if setor_limpo else "Não informado", unidade=unidade_formatada, telefone=telefone_limpo, numero_vip=proximo_numero_atual, evento="FUNCIONAL")
        
        if success:
            st.session_state.numero_vip_sucesso = proximo_numero_atual
            st.session_state.mostrar_caixa_sucesso = True
        else:
            st.session_state.mensagem_erro = f"Erro: {message}"
            st.session_state.mostrar_caixa_erro = True
    st.rerun()

total_final = contar_participantes()
vagas_restantes = 50 - total_final if total_final < 50 else 0

st.markdown(f"""
<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, rgba(255, 255, 255, 0.7), rgba(244, 114, 182, 0.4)); border-radius: 20px; border: 2px solid rgba(244, 114, 182, 0.5); margin-top: 1rem;'>
    <div style='font-size: 3.5rem; font-weight: 900; color: #be185d; text-shadow: 0 0 30px rgba(219, 39, 119, 0.5); margin-bottom: 0.5rem;'>{total_final}/50</div>
    <div style='color: #831843; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; font-size: 1.2rem; margin-bottom: 0.8rem;'>INSCRIÇÕES CONFIRMADAS</div>
""", unsafe_allow_html=True)

if total_final >= 50:
    st.markdown(f"""
    <div style='color: #ef4444; font-size: 1.1rem; font-weight: 900; background: rgba(255, 255, 255, 0.8); padding: 0.8rem 1.5rem; border-radius: 12px; display: inline-block; box-shadow: 0 0 20px rgba(239, 68, 68, 0.4); animation: pulse 2s infinite;'>🚫 VAGAS ESGOTADAS • {total_final}/50</div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style='color: #db2777; font-size: 1rem; font-weight: 700; background: rgba(255, 255, 255, 0.8); padding: 0.8rem 1.5rem; border-radius: 12px; display: inline-block; box-shadow: 0 0 20px rgba(219, 39, 119, 0.3);'>{vagas_restantes} VAGAS RESTANTES</div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; padding: 2rem 1rem; margin-top: 1.5rem; border-top: 2px solid rgba(244, 114, 182, 0.5); background: rgba(255, 255, 255, 0.7); border-radius: 0 0 30px 30px;">
    <div style="font-size: 3rem; font-weight: 900; color: #db2777; text-shadow: 0 0 40px rgba(219, 39, 119, 0.6); margin-bottom: 1rem;">CONFRA AULÃO FUNCIONAL</div>
    <div style="color: #be185d; margin-bottom: 0.8rem; font-size: 1.4rem; font-weight: 700;">💪 VAMOS CONTINUAR O MOVIMENTO!</div>
    <div style="color: #831843; font-size: 1rem; letter-spacing: 2px; margin-bottom: 0.5rem;">📍 Faixa de Areia Beira Mar - Meireles</div>
    <div style="color: #831843; font-size: 0.9rem; letter-spacing: 1px;">05 DE DEZEMBRO • 05:45 • 50 VAGAS</div>
    <div style="color: #db2777; font-size: 1rem; font-weight: 700; margin-top: 0.8rem; letter-spacing: 1px;">⏰ INSCRIÇÕES ABREM 25/11/2026 ÀS 12:00</div>
</div>
</div>
""", unsafe_allow_html=True)
