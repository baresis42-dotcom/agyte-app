import streamlit as st
from datetime import datetime
import time
import random
from streamlit.components.v1 import html
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# ==============================
# FUNÇÕES DE FORMATAÇÃO E VALIDAÇÃO
# ==============================
def formatar_cpf(cpf):
    """Remove caracteres não numéricos do CPF"""
    if not cpf:
        return ""
    return ''.join(filter(str.isdigit, cpf))

def formatar_telefone(telefone):
    """Remove caracteres não numéricos do telefone"""
    if not telefone:
        return ""
    return ''.join(filter(str.isdigit, telefone))

def get_connection():
    """Tenta conectar ao banco. Retorna None se falhar."""
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

def inserir_participante(nome, cpf, setor, unidade, telefone, numero_vip, evento="JUMP"):
    """Insere participante na tabela public.agyte_participantes"""
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

        cur.execute(sql, (
            nome.upper(),
            cpf,
            setor if setor else "Não informado",
            unidade,
            telefone,
            numero_vip,
            evento
        ))

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
    """Conta o total de participantes no banco - SEMPRE CONSULTA ATUALIZADA"""
    try:
        conn = get_connection()
        if conn is None:
            return 0
            
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM public.agyte_participantes WHERE evento = 'JUMP'")
        resultado = cur.fetchone()
        total = resultado[0] if resultado else 0
        
        cur.close()
        conn.close()
        return total
    except Exception as e:
        print(f"Erro ao contar participantes: {e}")
        return 0

def verificar_cpf_existente(cpf):
    """Verifica se CPF já está cadastrado no banco - CONSULTA ATUALIZADA"""
    try:
        conn = get_connection()
        if conn is None:
            return False
            
        cur = conn.cursor()
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        cur.execute("""
            SELECT COUNT(*) FROM public.agyte_participantes 
            WHERE evento = 'JUMP' 
            AND REPLACE(REPLACE(cpf, '.', ''), '-', '') = %s
        """, (cpf_limpo,))
        
        resultado = cur.fetchone()
        existe = resultado[0] > 0 if resultado else False
        
        cur.close()
        conn.close()
        return existe
    except Exception as e:
        print(f"Erro ao verificar CPF: {e}")
        return False

def obter_proximo_numero():
    """Obtém o próximo número VIP baseado no banco - CONSULTA ATUALIZADA"""
    try:
        conn = get_connection()
        if conn is None:
            return 1
            
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(MAX(numero_vip), 0) as ultimo_numero 
            FROM public.agyte_participantes 
            WHERE evento = 'JUMP'
        """)
        resultado = cur.fetchone()
        ultimo_numero = resultado[0] if resultado else 0
        
        cur.close()
        conn.close()
        return ultimo_numero + 1
    except Exception as e:
        print(f"Erro ao obter próximo número: {e}")
        return 1

# ==============================
# CONFIGURAÇÃO DO APP
# ==============================
st.set_page_config(
    page_title="AGYTE-SE | 4º ENCONTRO - JUMP",
    page_icon="💥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================
# CSS COMPLETO - TEMA JUMP (LARANJA/VERMELHO VIBRANTE)
# ==============================
st.markdown("""
<style>
    /* FUNDO COM GRADIENTE LARANJA/VERMELHO */
    .stApp {
        background: 
            linear-gradient(135deg, 
                #1a0a00 0%, 
                #c2410c 25%, 
                #ea580c 50%, 
                #c2410c 75%, 
                #1a0a00 100%);
        background-size: 400% 400%;
        animation: fluidGradient 12s ease infinite;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
        overflow-y: auto;
    }
    
    @keyframes fluidGradient {
        0% { background-position: 0% 50%; }
        25% { background-position: 50% 100%; }
        50% { background-position: 100% 50%; }
        75% { background-position: 50% 0%; }
        100% { background-position: 0% 50%; }
    }
    
    /* EFEITO DE VIBRAÇÃO - PERFEITO PRA JUMP! */
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
        20%, 40%, 60%, 80% { transform: translateX(10px); }
    }
    
    @keyframes jumpBounce {
        0%, 100% { transform: translateY(0); }
        20% { transform: translateY(-30px); }
        40% { transform: translateY(0); }
        60% { transform: translateY(-15px); }
        80% { transform: translateY(0); }
    }
    
    body.shake {
        animation: shake 0.6s cubic-bezier(.36,.07,.19,.97) both;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes blink {
        0%, 100% { 
            opacity: 1;
            box-shadow: 0 0 60px rgba(234, 88, 12, 0.8);
        }
        50% { 
            opacity: 0.9;
            box-shadow: 0 0 100px rgba(249, 115, 22, 1);
        }
    }
    
    @keyframes blinkRed {
        0%, 100% { 
            opacity: 1;
            box-shadow: 0 0 60px rgba(239, 68, 68, 0.8);
        }
        50% { 
            opacity: 0.9;
            box-shadow: 0 0 100px rgba(239, 68, 68, 1);
        }
    }
    
    @keyframes vipPulse {
        0% { 
            transform: scale(1);
            text-shadow: 0 0 40px rgba(255, 255, 255, 1);
        }
        100% { 
            transform: scale(1.1);
            text-shadow: 0 0 60px rgba(255, 255, 255, 1);
        }
    }
    
    @keyframes iconFloat {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(5deg); }
    }
    
    /* LINHAS ABSTRATAS */
    .abstract-lines {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        opacity: 0.15;
    }
    
    .line {
        position: absolute;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.8), 
            transparent);
        box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
        animation: lineMove 20s linear infinite;
    }
    
    @keyframes lineMove {
        0% { transform: translateX(-100%) rotate(0deg); }
        100% { transform: translateX(100vw) rotate(360deg); }
    }
    
    /* CONTAINER PRINCIPAL */
    .main-container {
        background: rgba(0, 0, 0, 0.75);
        backdrop-filter: blur(35px);
        -webkit-backdrop-filter: blur(35px);
        border-radius: 40px;
        border: 2px solid rgba(255, 255, 255, 0.15);
        box-shadow: 
            0 35px 70px rgba(0, 0, 0, 0.8),
            0 0 150px rgba(249, 115, 22, 0.3),
            inset 0 0 80px rgba(255, 255, 255, 0.03);
        padding: 3rem 2rem;
        margin: 1rem;
        position: relative;
        z-index: 10;
    }
    
    /* HEADER NOMES - ESTILO BOLINHA */
    .header-nomes {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 3rem;
        margin-bottom: 2.5rem;
        width: 100%;
        flex-wrap: wrap;
    }
    
    .nome-box {
        padding: 1.2rem 2.5rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
        text-align: center;
        min-width: 180px;
    }
    
    .nome-box:hover {
        transform: scale(1.08);
    }
    
    .nome-sesi-box {
        background: linear-gradient(135deg, #7c2d12 0%, #ea580c 100%);
        border: 3px solid rgba(251, 146, 60, 0.8);
        box-shadow: 
            0 0 50px rgba(234, 88, 12, 0.6),
            0 10px 30px rgba(0, 0, 0, 0.5),
            inset 0 0 30px rgba(255, 255, 255, 0.1);
        animation: glowOrange 3s infinite alternate;
    }
    
    @keyframes glowOrange {
        0% { box-shadow: 0 0 40px rgba(234, 88, 12, 0.5), 0 10px 30px rgba(0, 0, 0, 0.5); }
        100% { box-shadow: 0 0 70px rgba(251, 146, 60, 0.8), 0 15px 40px rgba(0, 0, 0, 0.6); }
    }
    
    .nome-dilady-box {
        background: linear-gradient(135deg, #9d174d 0%, #ec4899 100%);
        border: 3px solid rgba(244, 114, 182, 0.8);
        box-shadow: 
            0 0 50px rgba(236, 72, 153, 0.6),
            0 10px 30px rgba(0, 0, 0, 0.5),
            inset 0 0 30px rgba(255, 255, 255, 0.1);
        animation: glowPink 3s infinite alternate;
    }
    
    @keyframes glowPink {
        0% { box-shadow: 0 0 40px rgba(236, 72, 153, 0.5), 0 10px 30px rgba(0, 0, 0, 0.5); }
        100% { box-shadow: 0 0 70px rgba(244, 114, 182, 0.8), 0 15px 40px rgba(0, 0, 0, 0.6); }
    }
    
    .nome-sesi {
        font-size: 2.2rem;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 8px;
        text-shadow: 
            0 0 20px rgba(255, 255, 255, 0.8),
            0 0 40px rgba(249, 115, 22, 0.8),
            0 0 80px rgba(249, 115, 22, 0.5);
        font-family: 'Arial Black', 'Impact', sans-serif;
    }
    
    .nome-dilady {
        font-size: 2.2rem;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 4px;
        text-shadow: 
            0 0 20px rgba(255, 255, 255, 0.8),
            0 0 40px rgba(236, 72, 153, 0.8),
            0 0 80px rgba(236, 72, 153, 0.5);
        font-family: 'Georgia', 'Times New Roman', serif;
        font-style: italic;
    }
    
    /* CIRCLE HEADER */
    .circle-header {
        width: 220px;
        height: 220px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ea580c 0%, #f97316 40%, #fb923c 70%, #fdba74 100%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 1.5rem;
        box-shadow: 
            0 10px 30px rgba(234, 88, 12, 0.5),
            0 0 80px rgba(249, 115, 22, 0.6),
            0 0 100px rgba(251, 146, 60, 0.3),
            inset 0 0 40px rgba(255, 255, 255, 0.2);
        border: 3px solid rgba(255, 255, 255, 0.4);
        position: relative;
        overflow: hidden;
        animation: circlePulse 4s infinite alternate;
        margin: 0 auto;
    }
    
    @keyframes circlePulse {
        0% { 
            transform: scale(1);
            box-shadow: 0 10px 30px rgba(234, 88, 12, 0.5),
                        0 0 80px rgba(249, 115, 22, 0.6),
                        0 0 100px rgba(251, 146, 60, 0.3);
        }
        100% { 
            transform: scale(1.08);
            box-shadow: 0 20px 50px rgba(234, 88, 12, 0.7),
                        0 0 120px rgba(249, 115, 22, 0.9),
                        0 0 150px rgba(251, 146, 60, 0.5);
        }
    }
    
    .circle-header::before {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.15), transparent);
        animation: circleRotate 10s linear infinite;
    }
    
    @keyframes circleRotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .circle-header .programa {
        font-size: 1rem;
        font-weight: 800;
        color: white;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 0.3rem;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.9);
        position: relative;
        z-index: 1;
    }
    
    .circle-header .title {
        font-size: clamp(1.5rem, 5vw, 1.9rem);
        font-weight: 900;
        color: white;
        margin: 0.2rem 0;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-shadow: 
            0 0 20px rgba(255, 255, 255, 1),
            0 0 40px rgba(249, 115, 22, 0.8);
        position: relative;
        z-index: 1;
        line-height: 1.1;
    }
    
    .circle-header .subtitle {
        font-size: 0.85rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
        position: relative;
        z-index: 1;
        margin-top: 0.3rem;
    }
    
    /* EVENT BADGE */
    .event-badge {
        display: inline-block;
        background: linear-gradient(45deg, 
            rgba(234, 88, 12, 0.9), 
            rgba(249, 115, 22, 0.7));
        color: white;
        padding: 1.2rem 3rem;
        border-radius: 50px;
        font-weight: 900;
        letter-spacing: 4px;
        margin-top: 1.5rem;
        text-transform: uppercase;
        font-size: 1.2rem;
        border: 3px solid rgba(255, 255, 255, 0.7);
        box-shadow: 
            0 0 60px rgba(234, 88, 12, 0.8),
            0 0 80px rgba(249, 115, 22, 0.5),
            0 20px 50px rgba(0, 0, 0, 0.7);
        animation: badgeFloat 4s infinite ease-in-out;
    }
    
    @keyframes badgeFloat {
        0%, 100% { transform: translateY(0) scale(1); }
        50% { transform: translateY(-8px) scale(1.03); }
    }
    
    /* FORMULÁRIO PREMIUM */
    .form-container {
        background: rgba(0, 0, 0, 0.85);
        border-radius: 30px;
        padding: 3rem;
        margin: 2rem auto;
        max-width: 800px;
        border: 2px solid rgba(249, 115, 22, 0.5);
        box-shadow: 
            0 30px 80px rgba(0, 0, 0, 1),
            0 0 120px rgba(234, 88, 12, 0.4),
            inset 0 0 60px rgba(255, 255, 255, 0.03);
        position: relative;
        overflow: hidden;
    }
    
    .form-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            from 0deg at 50% 50%,
            rgba(234, 88, 12, 0.08) 0deg,
            rgba(249, 115, 22, 0.08) 90deg,
            rgba(251, 146, 60, 0.08) 180deg,
            rgba(234, 88, 12, 0.08) 270deg,
            rgba(234, 88, 12, 0.08) 360deg
        );
        animation: formRotate 20s linear infinite;
        z-index: -1;
    }
    
    @keyframes formRotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .form-title {
        color: #ffffff;
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 3px;
        text-shadow: 
            0 0 40px rgba(249, 115, 22, 0.9),
            0 0 80px rgba(251, 146, 60, 0.3);
        background: linear-gradient(45deg, #ffffff, #fed7aa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        position: relative;
        z-index: 2;
    }
    
    /* INPUTS PREMIUM */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(0, 0, 0, 0.9) !important;
        border: 2px solid rgba(249, 115, 22, 0.6) !important;
        border-radius: 15px !important;
        padding: 1.2rem !important;
        font-size: 1.2rem !important;
        color: #ffffff !important;
        box-shadow: 
            inset 0 0 30px rgba(249, 115, 22, 0.1),
            0 0 30px rgba(234, 88, 12, 0.3) !important;
        transition: all 0.3s ease !important;
        position: relative;
        z-index: 2;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #fb923c !important;
        box-shadow: 
            inset 0 0 40px rgba(249, 115, 22, 0.2),
            0 0 50px rgba(234, 88, 12, 0.6) !important;
        background: rgba(0, 0, 0, 1) !important;
        transform: scale(1.02);
    }
    
    .stTextInput label,
    .stSelectbox label {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        margin-bottom: 0.8rem !important;
        text-shadow: 0 0 20px rgba(249, 115, 22, 0.8);
        position: relative;
        z-index: 2;
    }
    
    /* BOTÃO PREMIUM - ESTILO JUMP */
    .stButton button {
        background: linear-gradient(45deg, 
            #ea580c 0%, 
            #f97316 50%, 
            #ea580c 100%) !important;
        background-size: 200% 100% !important;
        color: white !important;
        border: 4px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: 25px !important;
        padding: 1.8rem 3rem !important;
        font-size: 1.8rem !important;
        font-weight: 900 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 2rem !important;
        box-shadow: 
            0 0 120px rgba(249, 115, 22, 1),
            0 30px 90px rgba(0, 0, 0, 0.9),
            inset 0 0 50px rgba(255, 255, 255, 0.4) !important;
        animation: buttonPulse 1.2s infinite alternate, buttonShine 3s infinite;
        position: relative;
        overflow: hidden;
        z-index: 2;
        cursor: pointer !important;
        display: block !important;
        text-align: center !important;
    }
    
    .stButton button:hover {
        transform: scale(1.08) !important;
        box-shadow: 
            0 0 150px rgba(251, 146, 60, 1),
            0 35px 110px rgba(0, 0, 0, 1),
            inset 0 0 60px rgba(255, 255, 255, 0.5) !important;
        animation: jumpBounce 0.6s ease !important;
    }
    
    @keyframes buttonPulse {
        0% { transform: scale(1); }
        100% { transform: scale(1.05); }
    }
    
    @keyframes buttonShine {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    /* TEXTOS AUXILIARES - BRANCOS PARA LEGIBILIDADE */
    .texto-branco {
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    }
    
    .texto-destaque {
        color: #fbbf24 !important;
        font-weight: 800 !important;
    }
    
    .texto-laranja-claro {
        color: #fed7aa !important;
        font-weight: 700 !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .st-emotion-cache-1dp5vir {display: none;}
    
    /* MEDIA QUERIES */
    @media (max-width: 768px) {
        .main-container {
            margin: 0.5rem !important;
            padding: 1.5rem !important;
            border-radius: 25px !important;
        }
        
        .form-container {
            padding: 1.5rem !important;
            margin: 1rem auto !important;
            border-radius: 20px !important;
        }
        
        .form-title {
            font-size: 1.8rem !important;
        }
        
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            padding: 0.8rem !important;
            font-size: 1rem !important;
        }
        
        .stButton button {
            padding: 1rem 1.5rem !important;
            font-size: 1.2rem !important;
            letter-spacing: 2px !important;
        }
        
        .circle-header {
            width: 180px !important;
            height: 180px !important;
        }
        
        .header-nomes {
            gap: 1.5rem !important;
        }
        
        .nome-box {
            padding: 1rem 1.5rem !important;
            min-width: 140px !important;
        }
        
        .nome-sesi, .nome-dilady {
            font-size: 1.6rem !important;
        }
        
        .event-badge {
            padding: 0.8rem 1.5rem !important;
            font-size: 0.9rem !important;
        }
    }
    
    @media (max-width: 480px) {
        .main-container {
            padding: 1rem !important;
        }
        
        .circle-header {
            width: 150px !important;
            height: 150px !important;
        }
        
        .nome-sesi, .nome-dilady {
            font-size: 1.3rem !important;
        }
    }
    
</style>
""", unsafe_allow_html=True)

# ==============================
# LINHAS ABSTRATAS
# ==============================
st.markdown("""
<div class="abstract-lines">
    <div class="line" style="top: 12%; width: 350px; animation-delay: 0s; animation-duration: 25s;"></div>
    <div class="line" style="top: 38%; width: 450px; animation-delay: 4s; animation-duration: 22s;"></div>
    <div class="line" style="top: 62%; width: 400px; animation-delay: 8s; animation-duration: 28s;"></div>
    <div class="line" style="top: 88%; width: 300px; animation-delay: 12s; animation-duration: 20s;"></div>
    <div class="line" style="top: 28%; width: 250px; animation-delay: 16s; animation-duration: 24s;"></div>
</div>
""", unsafe_allow_html=True)

# ==============================
# CABEÇALHO PRINCIPAL
# ==============================
st.markdown("""
<div class="main-container">
    <div class="header-nomes">
        <div class="nome-box nome-sesi-box">
            <div class="nome-sesi">SESI</div>
        </div>
        <div class="nome-box nome-dilady-box">
            <div class="nome-dilady">DILADY</div>
        </div>
    </div>
    <div class="circle-header">
        <div class="programa">4º ENCONTRO</div>
        <div class="title">AGYTE-SE</div>
        <div class="subtitle">💥 JUMP 💥</div>
    </div>
    <div style="text-align: center;">
        <div class="event-badge">
            💥 PULE COM A GENTE! 💥
        </div>
    </div>
    <div style="margin-top: 2rem; color: #ffffff; font-size: 1.3rem; font-weight: 700; max-width: 700px; margin-left: auto; margin-right: auto; padding: 0 1rem; text-align: center;">
        Chegou o 4º Encontro do AGYTE-SE! Escolha sua modalidade e garanta sua vaga!
    </div>
""", unsafe_allow_html=True)

# ==============================
# INFORMAÇÕES DO EVENTO
# ==============================
st.markdown("""
    <div style='text-align: center; margin: 3rem 0;'>
        <div style='background: rgba(120, 45, 18, 0.4); 
                    border-radius: 25px; 
                    padding: 2rem;
                    border: 2px solid rgba(251, 146, 60, 0.5);
                    backdrop-filter: blur(15px);
                    box-shadow: 0 0 60px rgba(249, 115, 22, 0.3);'>
            <h2 style='color: #ffffff; margin-bottom: 1.5rem; font-size: 2.2rem; text-shadow: 0 0 20px rgba(249, 115, 22, 0.5);'>
                💥 4º ENCONTRO DO AGYTE-SE
            </h2>
            <div style='color: #ffffff; font-size: 1.2rem; line-height: 1.6; padding: 0 1rem;'>
                <div style='margin-bottom: 1rem;'>
                    📅 <span style='color: #fed7aa; font-weight: 700;'>Data:</span> 14 de Agosto
                </div>
                <div style='margin-bottom: 1rem;'>
                    ⏰ <span style='color: #fed7aa; font-weight: 700;'>Horário:</span> 18h00
                </div>
                <div style='margin-bottom: 1rem;'>
                    📍 <span style='color: #fed7aa; font-weight: 700;'>Local:</span> SENAI Parangaba
                </div>
                <div style='margin-bottom: 1.5rem;'>
                    💥 <span style='color: #fed7aa; font-weight: 900;'>Modalidade:</span> JUMP - 30 vagas
                </div>
                <div style='margin-top: 1rem; color: #fbbf24; font-weight: 800; font-size: 1.3rem;'>
                    ⏰ <span style='background: rgba(0,0,0,0.5); padding: 3px 12px; border-radius: 8px;'>INSCRIÇÕES: 11/08 às 12h</span>
                </div>
            </div>
        </div>
    </div>
    
    <div style='text-align: center; margin: 2rem 0;'>
        <div style='background: rgba(0, 0, 0, 0.5); 
                    border-radius: 20px; 
                    padding: 1.5rem;
                    border: 2px dashed rgba(251, 146, 60, 0.5);
                    backdrop-filter: blur(15px);'>
            <div style='color: #fed7aa; font-size: 1.1rem; font-weight: 700;'>
                🧘 <span style='color: #ffffff;'>Pilates também disponível!</span> 
                (40 vagas - Inscrições em 12/08 às 12h)
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==============================
# CONTADORES PREMIUM (30 VAGAS)
# ==============================
total_banco_atual = contar_participantes()
proximo_numero_atual = obter_proximo_numero()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style='background: rgba(0, 0, 0, 0.7); 
                border-radius: 25px; 
                padding: 2rem; 
                text-align: center;
                border: 2px solid rgba(249, 115, 22, 0.5);
                backdrop-filter: blur(15px);
                box-shadow: 0 0 50px rgba(249, 115, 22, 0.4);
                height: 100%;'>
        <div style='font-size: 4rem; 
                    font-weight: 900; 
                    color: #ffffff;
                    text-shadow: 0 0 30px #f97316;
                    margin-bottom: 0.8rem;'>
            {total_banco_atual}/30
        </div>
        <div style='color: #fed7aa; 
                    font-size: 1.2rem; 
                    text-transform: uppercase; 
                    letter-spacing: 3px;
                    font-weight: 700;'>
            INSCRITOS
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: rgba(0, 0, 0, 0.7); 
                border-radius: 25px; 
                padding: 2rem; 
                text-align: center;
                border: 2px solid rgba(251, 146, 60, 0.5);
                backdrop-filter: blur(15px);
                box-shadow: 0 0 50px rgba(251, 146, 60, 0.4);
                height: 100%;'>
        <div style='font-size: 3rem; color: #ffffff; margin-bottom: 1rem;'>💥</div>
        <div style='font-size: 1.2rem; color: #ffffff; font-weight: 900; margin-bottom: 0.5rem; line-height: 1.6;'>
            MODALIDADE<br>
            JUMP
        </div>
        <div style='color: #fed7aa; font-size: 1.5rem; font-weight: 700;'>
            30 VAGAS
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='background: rgba(0, 0, 0, 0.7); 
                border-radius: 25px; 
                padding: 2rem; 
                text-align: center;
                border: 2px solid rgba(253, 186, 116, 0.5);
                backdrop-filter: blur(15px);
                box-shadow: 0 0 50px rgba(253, 186, 116, 0.4);
                height: 100%;'>
        <div style='font-size: 3rem; color: #ffffff; margin-bottom: 1rem;'>📍</div>
        <div style='font-size: 1.1rem; color: #ffffff; font-weight: 900; margin-bottom: 0.5rem; line-height: 1.4;'>
            SENAI Parangaba<br>
            Fortaleza - CE
        </div>
        <div style='color: #fed7aa; font-size: 1.2rem; font-weight: 700;'>
            14/08 • 18h
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# FORMULÁRIO PREMIUM
# ==============================
st.markdown("""
<div class="form-container">
    <h2 class="form-title">💥 GARANTA SUA VAGA NO JUMP!</h2>
    <div style='color: #ffffff; text-align: center; margin-bottom: 3rem; font-weight: 700; letter-spacing: 2px; font-size: 1.2rem;'>
        4º ENCONTRO AGYTE-SE • 30 VAGAS
    </div>
""", unsafe_allow_html=True)

# Estado da sessão
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
        nome = st.text_input(
            "NOME COMPLETO *",
            placeholder="DIGITE SEU NOME",
            help="Nome para o credenciamento"
        )
    
    with col2:
        cpf_input = st.text_input(
            "CPF *",
            placeholder="000.000.000-00",
            help="Digite 11 números (somente números)",
            max_chars=14
        )
    
    # SETOR AGORA É LIVRE (TEXT INPUT)
    setor = st.text_input(
        "SETOR DE ATUAÇÃO",
        placeholder="Ex: TI, Comercial, Produção... (opcional)",
        help="Preencha se quiser, não é obrigatório"
    )
    
    unidade = st.selectbox(
        "UNIDADE *",
        ["🏢 DILADY", "💖 FINNA", "❤️ LOVE"]
    )
    
    telefone_input = st.text_input(
        "WHATSAPP *",
        placeholder="(85) 99999-9999",
        help="Digite números com DDD (somente números)",
        max_chars=15
    )
    
    # Caixas de mensagem
    if st.session_state.mostrar_caixa_sucesso:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, 
                rgba(234, 88, 12, 0.95) 0%, 
                rgba(249, 115, 22, 0.95) 100%);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            border: 3px solid rgba(255, 255, 255, 0.9);
            box-shadow: 
                0 0 60px rgba(249, 115, 22, 0.8),
                0 20px 50px rgba(0, 0, 0, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.2);
            animation: blink 1s infinite alternate;
            text-align: center;
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
        '>
            <div style='font-size: 3rem; margin-bottom: 1rem; animation: jumpBounce 1s infinite;'>💥</div>
            <div style='font-size: 2.2rem; font-weight: 900; color: #ffffff; margin-bottom: 1rem; text-shadow: 0 0 20px rgba(255, 255, 255, 0.8);'>
                ✅ INSCRIÇÃO CONFIRMADA!
            </div>
            <div style='font-size: 4rem; font-weight: 900; color: #ffffff; margin: 1rem 0; 
                      text-shadow: 0 0 30px rgba(255, 255, 255, 1);
                      background: linear-gradient(45deg, #ffffff, #fed7aa);
                      -webkit-background-clip: text;
                      -webkit-text-fill-color: transparent;
                      animation: vipPulse 1.5s infinite alternate;'>
                Nº {st.session_state.numero_vip_sucesso}
            </div>
            <div style='font-size: 1.5rem; color: #ffffff; font-weight: 700;'>
                VAGA GARANTIDA NO JUMP! 💥
            </div>
            <div style='font-size: 1.1rem; color: #ffffff; margin-top: 0.5rem;'>
                14/08 • 18h • SENAI Parangaba
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.mostrar_caixa_erro:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, 
                rgba(220, 38, 38, 0.95) 0%, 
                rgba(239, 68, 68, 0.95) 100%);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            border: 3px solid rgba(255, 255, 255, 0.9);
            box-shadow: 
                0 0 60px rgba(239, 68, 68, 0.8),
                0 20px 50px rgba(0, 0, 0, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.2);
            animation: blinkRed 1s infinite alternate;
            text-align: center;
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
        '>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>⚠️</div>
            <div style='font-size: 2rem; font-weight: 900; color: #ffffff; margin-bottom: 1rem;'>
                ATENÇÃO!
            </div>
            <div style='font-size: 1.6rem; color: #ffffff; font-weight: 700;'>
                {st.session_state.mensagem_erro}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Botão de submit
    submitted = st.form_submit_button(
        "💥 CLIQUE AQUI PRA GARANTIR SUA VAGA NO JUMP! 💥",
        use_container_width=True
    )

st.markdown("""
<div style="text-align: center; margin: 1.5rem 0; padding: 1.2rem; background: rgba(120, 45, 18, 0.3); border-radius: 15px; border: 3px dashed rgba(251, 146, 60, 0.5); box-shadow: 0 0 30px rgba(249, 115, 22, 0.3);">
    <div style="color: #ffffff; font-size: 1.3rem; font-weight: 900; margin-bottom: 0.8rem; text-transform: uppercase; letter-spacing: 1.5px;">
        ⚡ PREENCHA TODOS OS CAMPOS ACIMA ⚡
    </div>
    <div style="color: #ffffff; font-size: 1.1rem; font-weight: 700;">
        E CLIQUE NO BOTÃO LARANJA PARA FINALIZAR!
    </div>
</div>
</div>
""", unsafe_allow_html=True)

# ==============================
# PROCESSAMENTO DO FORMULÁRIO
# ==============================
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
    
    elif total_banco_atual >= 30:
        st.session_state.mensagem_erro = "VAGAS ESGOTADAS! Todas as 30 vagas do JUMP já foram preenchidas."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    elif verificar_cpf_existente(cpf_limpo):
        st.session_state.mensagem_erro = "Este CPF já está cadastrado no JUMP!"
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    else:
        unidade_formatada = unidade.replace("🏢", "").replace("💖", "").replace("❤️", "").strip()
        
        success, message = inserir_participante(
            nome=nome_limpo,
            cpf=cpf_limpo,
            setor=setor_limpo if setor_limpo else "Não informado",
            unidade=unidade_formatada,
            telefone=telefone_limpo,
            numero_vip=proximo_numero_atual,
            evento="JUMP"
        )
        
        if success:
            st.session_state.numero_vip_sucesso = proximo_numero_atual
            st.session_state.mostrar_caixa_sucesso = True
            
            html("""
            <script>
            document.body.classList.add("shake");
            setTimeout(() => document.body.classList.remove("shake"), 400);
            </script>
            """, height=0)
        else:
            st.session_state.mensagem_erro = f"Erro: {message}"
            st.session_state.mostrar_caixa_erro = True
    
    st.rerun()

# ==============================
# CONTADOR DE VAGAS (30 VAGAS)
# ==============================
total_final = contar_participantes()
vagas_restantes = 30 - total_final if total_final < 30 else 0

st.markdown(f"""
<div style='text-align: center; padding: 1.5rem; 
            background: linear-gradient(135deg, rgba(120, 45, 18, 0.4), rgba(234, 88, 12, 0.3));
            border-radius: 20px; 
            border: 2px solid rgba(255, 255, 255, 0.4);
            margin-top: 1rem;'>
    <div style='font-size: 3.5rem; font-weight: 900; 
                background: linear-gradient(45deg, #ffffff, #fed7aa, #ffffff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
                text-shadow: 0 0 40px rgba(249, 115, 22, 0.6);'>
        {total_final}/30
    </div>
    <div style='color: #ffffff; 
                font-weight: 800; 
                letter-spacing: 3px;
                text-transform: uppercase;
                font-size: 1.2rem;
                margin-bottom: 0.8rem;'>
        INSCRIÇÕES CONFIRMADAS
    </div>
""", unsafe_allow_html=True)

if total_final >= 30:
    st.markdown(f"""
    <div style='color: #ef4444; 
                font-size: 1.1rem; 
                font-weight: 900;
                background: rgba(0, 0, 0, 0.5);
                padding: 0.8rem 1.5rem;
                border-radius: 12px;
                display: inline-block;
                box-shadow: 0 0 15px rgba(239, 68, 68, 0.5);
                animation: pulse 2s infinite;'>
        🚫 VAGAS ESGOTADAS • {total_final}/30
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style='color: #fed7aa; 
                font-size: 1rem; 
                font-weight: 700;
                background: rgba(0, 0, 0, 0.5);
                padding: 0.8rem 1.5rem;
                border-radius: 12px;
                display: inline-block;
                box-shadow: 0 0 15px rgba(249, 115, 22, 0.4);'>
        {vagas_restantes} VAGAS RESTANTES
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# RODAPÉ
# ==============================
st.markdown("""
<div style="text-align: center; padding: 2rem 1rem; margin-top: 1.5rem; 
            border-top: 2px solid rgba(249, 115, 22, 0.5);
            background: rgba(0, 0, 0, 0.5);
            border-radius: 0 0 30px 30px;">
    <div style="font-size: 3rem; font-weight: 900; 
                background: linear-gradient(45deg, #ea580c, #f97316, #ea580c);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1rem;
                text-shadow: 0 0 40px rgba(249, 115, 22, 0.7);">
        AGYTE-SE JUMP
    </div>
    <div style="color: #ffffff; margin-bottom: 0.8rem; font-size: 1.4rem; font-weight: 700;">
        4º ENCONTRO • 💥 JUMP • SENAI PARANGABA
    </div>
    <div style="color: #ffffff; font-size: 1rem; letter-spacing: 2px; margin-bottom: 0.5rem;">
        📍 SENAI Parangaba - Fortaleza/CE
    </div>
    <div style="color: #ffffff; font-size: 0.9rem; letter-spacing: 1px;">
        14 DE AGOSTO • 18H00 • 30 VAGAS
    </div>
    <div style="color: #fbbf24; font-size: 1rem; font-weight: 700; margin-top: 0.8rem; letter-spacing: 1px;">
        ⏰ INSCRIÇÕES ABREM 11/08 ÀS 12H
    </div>
    <div style="color: #fed7aa; font-size: 0.9rem; margin-top: 0.5rem;">
        🧘 Pilates: 40 vagas • Inscrições 12/08 às 12h
    </div>
</div>
</div>
""", unsafe_allow_html=True)
