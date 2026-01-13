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
            connect_timeout=3  # evita travar por muito tempo
        )
        return conn
    except:
        return None


def inserir_participante(nome, cpf, setor, unidade, telefone, numero_vip, evento="FUNCIONAL"):
    """Insere participante na tabela public.agyte_participantes"""
    try:
        conn = get_connection()
        if conn is None:
            # Banco inacessível: apenas simula sucesso
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
            setor,
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
        cur.execute("SELECT COUNT(*) as total FROM public.agyte_participantes WHERE evento = 'FUNCIONAL'")
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
        
        # Consulta direta com o CPF formatado
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
            WHERE evento = 'FUNCIONAL'
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
    page_title="AGYTE-SE | LANÇAMENTO FITNESS DILADY",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================
# CSS COMPLETO (MANTIDO COM AJUSTES DE RESPONSIVIDADE)
# ==============================
st.markdown("""
<style>
    /* FUNDO COM GRADIENTE FLUIDO ROSA/LILÁS */
    .stApp {
        background: 
            linear-gradient(125deg, 
                #ff1493 0%, 
                #ff69b4 25%, 
                #da70d6 50%, 
                #9370db 75%, 
                #8a2be2 100%);
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
    
    /* EFEITO DE VIBRAÇÃO */
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
        20%, 40%, 60%, 80% { transform: translateX(10px); }
    }
    
    body.shake {
        animation: shake 0.6s cubic-bezier(.36,.07,.19,.97) both;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* ANIMAÇÃO DE PISCAR */
    @keyframes blink {
        0%, 100% { 
            opacity: 1;
            box-shadow: 0 0 60px rgba(76, 175, 80, 0.8);
        }
        50% { 
            opacity: 0.9;
            box-shadow: 0 0 100px rgba(76, 175, 80, 1);
        }
    }
    
    /* =============================
       CAIXA DE SUCESSO GRANDE E PISCANTE
    ============================= */
    .success-box-big {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, 
            rgba(76, 175, 80, 0.95) 0%, 
            rgba(56, 142, 60, 0.95) 100%);
        border-radius: 25px;
        padding: 3rem 4rem;
        z-index: 9999;
        border: 4px solid rgba(255, 255, 255, 0.9);
        box-shadow: 
            0 0 80px rgba(76, 175, 80, 0.8),
            0 30px 70px rgba(0, 0, 0, 0.9),
            inset 0 0 40px rgba(255, 255, 255, 0.2);
        animation: blink 1.5s infinite alternate,
                   popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-align: center;
        min-width: 500px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
    
    @keyframes popIn {
        0% { 
            transform: translate(-50%, -50%) scale(0.3);
            opacity: 0;
        }
        70% { 
            transform: translate(-50%, -50%) scale(1.05);
            opacity: 1;
        }
        100% { 
            transform: translate(-50%, -50%) scale(1);
            opacity: 1;
        }
    }
    
    .success-title {
        font-size: 2.8rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        margin-bottom: 1.5rem !important;
        text-shadow: 
            0 0 30px rgba(255, 255, 255, 0.8),
            0 0 60px rgba(76, 175, 80, 0.5);
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .success-vip {
        font-size: 4.5rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        margin: 1rem 0 !important;
        text-shadow: 
            0 0 40px rgba(255, 255, 255, 1),
            0 0 80px rgba(76, 175, 80, 0.8);
        background: linear-gradient(45deg, #ffffff, #a5d6a7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: vipPulse 2s infinite alternate;
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
    
    .success-subtitle {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        margin-top: 1.5rem !important;
        text-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
        letter-spacing: 1px;
    }
    
    .success-icon {
        font-size: 5rem !important;
        margin-bottom: 1rem !important;
        animation: iconFloat 3s infinite ease-in-out;
    }
    
    @keyframes iconFloat {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(5deg); }
    }
    
    /* CAIXA DE ERRO */
    .error-box {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, 
            rgba(244, 67, 54, 0.95) 0%, 
            rgba(211, 47, 47, 0.95) 100%);
        border-radius: 25px;
        padding: 3rem 4rem;
        z-index: 9999;
        border: 4px solid rgba(255, 255, 255, 0.9);
        box-shadow: 
            0 0 80px rgba(244, 67, 54, 0.8),
            0 30px 70px rgba(0, 0, 0, 0.9),
            inset 0 0 40px rgba(255, 255, 255, 0.2);
        animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-align: center;
        min-width: 500px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
    
    /* =============================
       MEDIA QUERIES RESPONSIVAS - APENAS AJUSTES NECESSÁRIOS
    ============================= */
    @media (max-width: 768px) {
        .success-box-big,
        .error-box {
            min-width: 300px;
            padding: 2rem;
            margin: 1rem;
        }
        
        .success-title {
            font-size: 2rem !important;
        }
        
        .success-vip {
            font-size: 3rem !important;
        }
        
        .success-subtitle {
            font-size: 1.3rem !important;
        }
        
        .success-icon {
            font-size: 3.5rem !important;
        }
        
        .main-container {
            margin: 0.5rem !important;
            padding: 1.5rem !important;
            border-radius: 25px !important;
        }
        
        .header-container {
            padding: 1.5rem !important;
            border-radius: 20px !important;
            margin-bottom: 1.5rem !important;
        }
        
        .title-text {
            font-size: 2.8rem !important;
            letter-spacing: -1px !important;
        }
        
        .subtitle-text {
            font-size: 1.2rem !important;
            letter-spacing: 3px !important;
        }
        
        .event-badge {
            padding: 0.8rem 1.5rem !important;
            font-size: 0.9rem !important;
            letter-spacing: 2px !important;
            margin-top: 1rem !important;
        }
        
        .form-container {
            padding: 1.5rem !important;
            margin: 1rem auto !important;
            border-radius: 20px !important;
        }
        
        .form-title {
            font-size: 1.8rem !important;
        }
        
        /* AJUSTES PARA COLUNAS EM MOBILE - APENAS TAMANHO */
        .st-emotion-cache-1r6slb0 {
            flex-direction: column;
            gap: 1rem;
        }
        
        .st-emotion-cache-1r6slb0 > div {
            width: 100% !important;
        }
        
        /* INPUTS EM MOBILE */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            padding: 0.8rem !important;
            font-size: 1rem !important;
        }
        
        /* BOTÃO EM MOBILE */
        .stButton button {
            padding: 1rem 1.5rem !important;
            font-size: 1.2rem !important;
            letter-spacing: 2px !important;
            margin-top: 1rem !important;
        }
        
        /* AJUSTE DO CÍRCULO EM MOBILE */
        .circle-header {
            width: 180px !important;
            height: 180px !important;
        }
        
        .circle-header .agyte-juntos {
            font-size: 1.8rem !important;
        }
        
        .circle-header .juntos {
            font-size: 0.85rem !important;
        }
    }
    
    @media (max-width: 480px) {
        .success-box-big,
        .error-box {
            min-width: 280px;
            padding: 1.5rem;
        }
        
        .success-title {
            font-size: 1.6rem !important;
        }
        
        .success-vip {
            font-size: 2.5rem !important;
        }
        
        .title-text {
            font-size: 2.2rem !important;
        }
        
        .subtitle-text {
            font-size: 1rem !important;
            letter-spacing: 2px !important;
        }
        
        .form-title {
            font-size: 1.5rem !important;
        }
        
        .main-container {
            padding: 1rem !important;
            margin: 0.25rem !important;
        }
        
        .circle-header {
            width: 150px !important;
            height: 150px !important;
        }
        
        .circle-header .agyte-juntos {
            font-size: 1.5rem !important;
        }
        
        .circle-header .juntos {
            font-size: 0.75rem !important;
        }
        
        .food-donation {
            padding: 0.8rem !important;
            font-size: 0.9rem !important;
            margin: 1rem auto !important;
            max-width: 95% !important;
        }
    }
    
    /* =============================
       CENA GYM REAL - MANTIDO IGUAL
    ============================= */
    .gym-real {
        position: fixed;
        inset: 0;
        z-index: 0;
        overflow: hidden;
        pointer-events: none;
    }
    
    /* =============================
       HALTER REALISTA COM LATERAIS MAIORES
    ============================= */
    .real-dumbbell {
        position: absolute;
        width: 480px;
        height: 160px;
        left: 8%;
        top: 20%;
        animation: floatDumbbell 6s ease-in-out infinite,
                   rotateDumbbell 25s linear infinite;
        transform-origin: center center;
    }
    
    /* Barra - MAIS LONGA */
    .real-dumbbell .bar {
        position: absolute;
        left: 100px;
        right: 100px;
        top: 50%;
        height: 24px;
        transform: translateY(-50%);
        background: linear-gradient(90deg, 
            #333 0%,
            #666 20%,
            #999 40%,
            #ccc 50%,
            #999 60%,
            #666 80%,
            #333 100%);
        border-radius: 12px;
        box-shadow: 
            inset 0 0 20px rgba(0,0,0,0.8),
            0 0 25px rgba(0,0,0,0.7),
            0 0 50px rgba(255, 20, 147, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.1);
        z-index: 2;
    }
    
    /* Grupo de anilhas - LATERAIS MAIORES */
    .weight-stack {
        position: absolute;
        width: 120px;
        height: 100%;
        display: flex;
        gap: 10px;
        align-items: center;
        z-index: 1;
    }
    
    .weight-stack.left { 
        left: 0; 
        justify-content: flex-end;
    }
    
    .weight-stack.right { 
        right: 0; 
        justify-content: flex-start;
    }
    
    /* Anilha circular - MAIOR E MAIS ESPESSA */
    .weight {
        width: 55px;
        height: 110px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, 
            #666 0%,
            #444 30%,
            #222 60%,
            #000 100%);
        box-shadow:
            inset 0 0 20px rgba(255,255,255,0.15),
            inset 0 0 35px rgba(0,0,0,0.6),
            0 12px 30px rgba(0,0,0,0.8),
            0 0 25px rgba(255, 20, 147, 0.15);
        border: 3px solid rgba(255,255,255,0.1);
        position: relative;
        overflow: hidden;
    }
    
    /* Detalhes das anilhas */
    .weight::before {
        content: "";
        position: absolute;
        inset: 12px;
        border-radius: 50%;
        background: radial-gradient(circle, #111, #000);
        box-shadow: inset 0 0 12px rgba(0,0,0,0.8);
    }
    
    /* Anilha individual com marcação */
    .weight:nth-child(1)::after {
        content: "20";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: rgba(255,255,255,0.25);
        font-weight: 900;
        font-size: 16px;
        font-family: 'Arial Black', sans-serif;
        text-shadow: 1px 1px 0 rgba(0,0,0,0.8);
    }
    
    .weight:nth-child(2)::after {
        content: "10";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: rgba(255,255,255,0.25);
        font-weight: 900;
        font-size: 16px;
        font-family: 'Arial Black', sans-serif;
        text-shadow: 1px 1px 0 rgba(0,0,0,0.8);
    }
    
    .weight:nth-child(3)::after {
        content: "5";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: rgba(255,255,255,0.25);
        font-weight: 900;
        font-size: 14px;
        font-family: 'Arial Black', sans-serif;
        text-shadow: 1px 1px 0 rgba(0,0,0,0.8);
    }
    
    /* =============================
       ANILHA OCTOGONAL REAL - MAIOR
    ============================= */
    .real-plate {
        position: absolute;
        width: 240px;
        height: 240px;
        right: 8%;
        bottom: 12%;
        background: linear-gradient(145deg, 
            #444 0%,
            #222 30%,
            #000 100%);
        clip-path: polygon(
            30% 0%, 70% 0%,
            100% 30%, 100% 70%,
            70% 100%, 30% 100%,
            0% 70%, 0% 30%
        );
        box-shadow:
            inset 0 0 35px rgba(255,255,255,0.12),
            inset 0 0 70px rgba(0,0,0,0.7),
            0 30px 70px rgba(0,0,0,0.9),
            0 0 90px rgba(255, 20, 147, 0.3);
        animation: floatPlate 7s ease-in-out infinite,
                   rotateReverse 35s linear infinite;
        border: 4px solid rgba(255,255,255,0.08);
        transform-origin: center center;
    }
    
    /* Furo central - MAIOR */
    .real-plate::before {
        content: "";
        position: absolute;
        inset: 85px;
        border-radius: 50%;
        background: radial-gradient(circle, #111, #000);
        box-shadow: 
            inset 0 0 25px rgba(0,0,0,0.9),
            0 0 30px rgba(0,0,0,0.6);
        border: 3px solid rgba(255,255,255,0.05);
    }
    
    /* Marcação - MAIOR */
    .real-plate::after {
        content: "35";
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        font-weight: 900;
        color: rgba(255,255,255,0.3);
        font-family: 'Arial Black', sans-serif;
        text-shadow: 
            3px 3px 0 rgba(0,0,0,0.9),
            -1px -1px 0 rgba(255,255,255,0.1);
        letter-spacing: 3px;
    }
    
    .real-plate .kg {
        position: absolute;
        bottom: 32%;
        left: 50%;
        transform: translateX(-50%);
        font-size: 18px;
        font-weight: 900;
        color: rgba(255,255,255,0.25);
        letter-spacing: 3px;
        text-shadow: 2px 2px 0 rgba(0,0,0,0.8);
    }
    
    /* =============================
       ANIMAÇÕES - MANTIDAS IGUAIS
    ============================= */
    @keyframes floatDumbbell {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        25% { transform: translate(-20px, -30px) rotate(5deg); }
        50% { transform: translate(15px, -20px) rotate(-2deg); }
        75% { transform: translate(-10px, 25px) rotate(3deg); }
    }
    
    @keyframes floatPlate {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(25px, -25px) rotate(-5deg); }
        66% { transform: translate(-15px, 20px) rotate(4deg); }
    }
    
    @keyframes rotateDumbbell {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }
    
    @keyframes rotateReverse {
        from { transform: rotate(0deg); }
        to   { transform: rotate(-360deg); }
    }
    
    /* LINHAS ABSTRATAS RESPONSIVAS */
    .abstract-lines {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        opacity: 0.3;
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
    
    /* LOGO DILADY SEM O BACKGROUND BRANCO DE "ATHLETIC" */
    .dilady-logo {
        position: relative;
        font-family: 'Playfair Display', 'Georgia', serif;
        font-weight: 900;
        font-size: 3.5rem;
        background: linear-gradient(45deg, 
            #ff1493 0%, 
            #ff69b4 33%, 
            #da70d6 66%, 
            #8a2be2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 
            0 5px 20px rgba(255, 20, 147, 0.5),
            0 10px 40px rgba(138, 43, 226, 0.3);
        letter-spacing: 2px;
        margin-bottom: 1.5rem;
    }
    
    /* REMOVENDO O RETÂNGULO BRANCO DE ATHLETIC */
    .dilady-logo::after {
        content: none;
    }
    
    /* CONTAINER PRINCIPAL COM NEON EFFECT RESPONSIVO */
    .main-container {
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(35px);
        -webkit-backdrop-filter: blur(35px);
        border-radius: 40px;
        border: 2px solid rgba(255, 255, 255, 0.15);
        box-shadow: 
            0 35px 70px rgba(0, 0, 0, 0.8),
            0 0 150px rgba(255, 20, 147, 0.3),
            inset 0 0 80px rgba(255, 255, 255, 0.05);
        padding: 3rem 2rem;
        margin: 1rem;
        position: relative;
        z-index: 10;
    }
    
    /* HEADER RESPONSIVO */
    .header-container {
        text-align: center;
        padding: 2.5rem 1rem;
        background: linear-gradient(135deg, 
            rgba(255, 20, 147, 0.15) 0%, 
            rgba(218, 112, 214, 0.2) 50%,
            rgba(138, 43, 226, 0.15) 100%);
        border-radius: 30px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.1), 
            transparent);
        animation: headerShine 8s infinite;
    }
    
    @keyframes headerShine {
        100% { left: 100%; }
    }
    
    .title-text {
        font-size: 4.5rem;
        font-weight: 900;
        background: linear-gradient(45deg, 
            #ffffff 0%, 
            #ffb6c1 20%, 
            #ff69b4 40%, 
            #da70d6 60%, 
            #9370db 80%, 
            #ffffff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 
            0 0 50px rgba(255, 20, 147, 0.7),
            0 0 100px rgba(138, 43, 226, 0.5);
        margin: 0;
        letter-spacing: -2px;
        text-transform: uppercase;
        font-family: 'Montserrat', 'Arial Black', sans-serif;
        animation: titlePulse 4s infinite alternate;
    }
    
    @keyframes titlePulse {
        0% { 
            filter: drop-shadow(0 0 40px rgba(255, 20, 147, 0.8));
            background-size: 100% 100%;
        }
        100% { 
            filter: drop-shadow(0 0 60px rgba(138, 43, 226, 0.9));
            background-size: 150% 150%;
        }
    }
    
    .subtitle-text {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: 6px;
        margin-top: 1rem;
        text-transform: uppercase;
        text-shadow: 
            0 0 30px rgba(255, 255, 255, 0.9),
            0 0 60px rgba(255, 105, 180, 0.5);
        animation: subtitleGlow 3s infinite alternate;
    }
    
    @keyframes subtitleGlow {
        0% { opacity: 0.9; }
        100% { opacity: 1; }
    }
    
    .event-badge {
        display: inline-block;
        background: linear-gradient(45deg, 
            rgba(255, 20, 147, 0.9), 
            rgba(218, 112, 214, 0.9));
        color: white;
        padding: 1.2rem 3rem;
        border-radius: 50px;
        font-weight: 900;
        letter-spacing: 4px;
        margin-top: 2rem;
        text-transform: uppercase;
        font-size: 1.2rem;
        border: 3px solid rgba(255, 255, 255, 0.6);
        box-shadow: 
            0 0 60px rgba(255, 20, 147, 0.8),
            0 20px 50px rgba(0, 0, 0, 0.7);
        animation: badgeFloat 4s infinite ease-in-out;
    }
    
    @keyframes badgeFloat {
        0%, 100% { transform: translateY(0) scale(1); }
        50% { transform: translateY(-15px) scale(1.05); }
    }
    
    /* FORMULÁRIO PREMIUM RESPONSIVO */
    .form-container {
        background: rgba(0, 0, 0, 0.9);
        border-radius: 30px;
        padding: 3rem;
        margin: 2rem auto;
        max-width: 800px;
        border: 2px solid rgba(255, 105, 180, 0.4);
        box-shadow: 
            0 30px 80px rgba(0, 0, 0, 1),
            0 0 120px rgba(255, 20, 147, 0.4),
            inset 0 0 60px rgba(255, 255, 255, 0.05);
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
            rgba(255, 20, 147, 0.1) 0deg,
            rgba(218, 112, 214, 0.1) 90deg,
            rgba(138, 43, 226, 0.1) 180deg,
            rgba(255, 20, 147, 0.1) 270deg,
            rgba(255, 20, 147, 0.1) 360deg
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
            0 0 40px rgba(255, 20, 147, 0.9),
            0 0 80px rgba(218, 112, 214, 0.5);
        background: linear-gradient(45deg, #ffffff, #ffb6c1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        position: relative;
        z-index: 2;
    }
    
    /* INPUTS PREMIUM RESPONSIVOS */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(0, 0, 0, 0.9) !important;
        border: 2px solid rgba(255, 105, 180, 0.5) !important;
        border-radius: 15px !important;
        padding: 1.2rem !important;
        font-size: 1.2rem !important;
        color: #ffffff !important;
        box-shadow: 
            inset 0 0 30px rgba(255, 105, 180, 0.15),
            0 0 30px rgba(255, 20, 147, 0.3) !important;
        transition: all 0.3s ease !important;
        position: relative;
        z-index: 2;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #ff1493 !important;
        box-shadow: 
            inset 0 0 40px rgba(255, 20, 147, 0.25),
            0 0 50px rgba(255, 20, 147, 0.5) !important;
        background: rgba(0, 0, 0, 1) !important;
        transform: scale(1.02);
    }
    
    .stTextInput label,
    .stSelectbox label {
        color: #ffb6c1 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        margin-bottom: 0.8rem !important;
        text-shadow: 0 0 20px rgba(255, 20, 147, 0.8);
        position: relative;
        z-index: 2;
    }
    
    /* MENSAGENS */
    .success-message {
        color: #4CAF50 !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-top: 1rem !important;
        padding: 1rem !important;
        background: rgba(76, 175, 80, 0.1) !important;
        border-radius: 10px !important;
        border-left: 4px solid #4CAF50 !important;
        text-align: center !important;
    }
    
    .error-message {
        color: #ff6b6b !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-top: 1rem !important;
        padding: 1rem !important;
        background: rgba(255, 107, 107, 0.1) !important;
        border-radius: 10px !important;
        border-left: 4px solid #ff6b6b !important;
        text-align: center !important;
    }
    
    /* BOTÃO PREMIUM RESPONSIVO - MELHORADO E MAIOR */
    .stButton button {
        background: linear-gradient(45deg, 
            #ff1493 0%, 
            #da70d6 50%, 
            #ff1493 100%) !important;
        background-size: 200% 100% !important;
        color: white !important;
        border: 4px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: 25px !important;
        padding: 1.8rem 3rem !important; /* MAIOR */
        font-size: 1.8rem !important; /* MAIOR */
        font-weight: 900 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 2rem !important;
        box-shadow: 
            0 0 120px rgba(255, 20, 147, 1),
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
        transform: scale(1.08) !important; /* MAIOR NO HOVER */
        box-shadow: 
            0 0 150px rgba(218, 112, 214, 1),
            0 35px 110px rgba(0, 0, 0, 1),
            inset 0 0 60px rgba(255, 255, 255, 0.5) !important;
    }
    
    @keyframes buttonPulse {
        0% { 
            transform: scale(1);
        }
        100% { 
            transform: scale(1.05);
        }
    }
    
    @keyframes buttonShine {
        0%, 100% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
    }
    
    /* TEXTO DO BOTÃO COM INDICAÇÃO CLARA */
    .button-text {
        display: block;
        position: relative;
        z-index: 2;
        text-shadow: 0 0 25px rgba(255, 255, 255, 0.9);
    }
    
    .button-text::after {
        content: "⬇️ CLIQUE AGORA! ⬇️";
        display: block;
        font-size: 1.1rem;
        font-weight: 900;
        margin-top: 0.8rem;
        letter-spacing: 2px;
        color: rgba(255, 255, 255, 1);
        animation: arrowBlink 1.5s infinite;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.9);
        background: rgba(0, 0, 0, 0.3);
        padding: 0.5rem;
        border-radius: 10px;
        border: 2px dashed rgba(255, 255, 255, 0.6);
    }
    
    @keyframes arrowBlink {
        0%, 100% { 
            opacity: 1;
            transform: scale(1);
        }
        50% { 
            opacity: 0.8;
            transform: scale(1.05);
        }
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .st-emotion-cache-1dp5vir {display: none;}
    
    /* CONTADOR MAIS PRÓXIMO */
    .counter-container {
        margin-top: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* RODAPÉ MAIS PRÓXIMO */
    .footer-container {
        margin-top: 2rem !important;
    }
    
    /* MENSAGEM DE DOAÇÃO DE ALIMENTOS */
    .food-donation {
        background: linear-gradient(135deg, 
            rgba(255, 215, 0, 0.2) 0%, 
            rgba(255, 165, 0, 0.2) 100%);
        border: 3px solid #FFD700;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 2rem auto;
        text-align: center;
        max-width: 600px;
        box-shadow: 
            0 0 50px rgba(255, 215, 0, 0.4),
            0 15px 40px rgba(0, 0, 0, 0.3);
        animation: donationGlow 3s infinite alternate;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    
    @keyframes donationGlow {
        0% { 
            box-shadow: 0 0 50px rgba(255, 215, 0, 0.4),
                       0 15px 40px rgba(0, 0, 0, 0.3);
        }
        100% { 
            box-shadow: 0 0 70px rgba(255, 165, 0, 0.6),
                       0 20px 50px rgba(0, 0, 0, 0.4);
        }
    }
    
    .food-icon {
        font-size: 3rem;
        margin-bottom: 0.8rem;
        display: block;
    }
    
    .food-title {
        color: #FFD700;
        font-size: 1.8rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
    }
    
    .food-description {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1.1rem;
        font-weight: 600;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# ELEMENTOS DE CENA DE ACADEMIA COM HALTERES MAIORES
# ==============================
st.markdown("""
<div class="abstract-lines">
    <div class="line" style="top: 12%; width: 350px; animation-delay: 0s; animation-duration: 25s;"></div>
    <div class="line" style="top: 38%; width: 450px; animation-delay: 4s; animation-duration: 22s;"></div>
    <div class="line" style="top: 62%; width: 400px; animation-delay: 8s; animation-duration: 28s;"></div>
    <div class="line" style="top: 88%; width: 300px; animation-delay: 12s; animation-duration: 20s;"></div>
    <div class="line" style="top: 28%; width: 250px; animation-delay: 16s; animation-duration: 24s;"></div>
</div>

<div class="gym-real">
    <div class="real-dumbbell">
        <div class="weight-stack left">
            <div class="weight"></div>
            <div class="weight"></div>
            <div class="weight"></div>
        </div>
        <div class="bar"></div>
        <div class="weight-stack right">
            <div class="weight"></div>
            <div class="weight"></div>
            <div class="weight"></div>
        </div>
    </div>
    <div class="real-plate">
        <div class="kg">KG</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# CABEÇALHO COM BOLA ROSCA LILÁS E ROSA - AJUSTADO
# ==============================

st.markdown("""
<style>
.main-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 1rem;
}

.circle-header {
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 50%, #9370DB 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 1.5rem;
    box-shadow: 
        0 10px 30px rgba(255, 20, 147, 0.4),
        0 0 80px rgba(218, 112, 214, 0.6),
        inset 0 0 40px rgba(255, 255, 255, 0.2);
    border: 3px solid rgba(255, 255, 255, 0.3);
    position: relative;
    overflow: hidden;
    animation: circlePulse 4s infinite alternate;
}

@keyframes circlePulse {
    0% { 
        transform: scale(1);
        box-shadow: 0 10px 30px rgba(255, 20, 147, 0.4),
                    0 0 80px rgba(218, 112, 214, 0.6);
    }
    100% { 
        transform: scale(1.05);
        box-shadow: 0 15px 40px rgba(255, 20, 147, 0.6),
                    0 0 100px rgba(218, 112, 214, 0.8);
    }
}

.circle-header::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    animation: circleRotate 10s linear infinite;
}

@keyframes circleRotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.circle-header .programa {
    font-size: 1.1rem;
    font-weight: 700;
    color: white;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 0.5rem;
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.8);
    position: relative;
    z-index: 1;
    line-height: 1;
}

.circle-header .agyte {
    font-size: clamp(1.3rem, 5.8vw, 2.2rem); /* reduz no mobile */
    font-weight: 900;
    color: white;
    margin: 0.3rem 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;

    text-shadow: 
        0 0 20px rgba(255, 255, 255, 0.9),
        0 0 40px rgba(255, 20, 147, 0.7);

    display: flex;
    justify-content: center;
    align-items: center;

    width: 100%;
    text-align: center;
    line-height: 1;

    white-space: nowrap;     /* 🔴 OBRIGA FICAR NA MESMA LINHA */
    overflow: hidden;        /* segurança */
}

.circle-header .juntos {
    font-size: 0.9rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    letter-spacing: 1.5px;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.6);
    position: relative;
    z-index: 1;
    margin-top: 0.3rem;
    line-height: 1;
    text-align: center;
}

.event-badge {
    margin-top: 1.5rem;
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(45deg, rgba(255, 20, 147, 0.8), rgba(218, 112, 214, 0.8));
    padding: 0.8rem 2rem;
    border-radius: 30px;
    border: 2px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 0 40px rgba(255, 20, 147, 0.5);
    animation: badgeFloat 4s infinite ease-in-out;
}

@keyframes badgeFloat {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-8px) scale(1.03); }
}
</style>

<div class="main-container">
    <div class="circle-header">
        <div class="programa">PROGRAMA</div>
        <div class="agyte">AGYTE-SE</div>
        <div class="juntos">JUNTOS EM MOVIMENTO</div>
    </div>
    <div class="event-badge">
        🏋️‍♀️ EVENTO EXCLUSIVO PARA COLABORADORES 🏋️‍♂️
    </div>
    <div style="margin-top: 2rem; color: rgba(255, 255, 255, 0.95); font-size: 1.3rem; font-weight: 600; max-width: 700px; margin-left: auto; margin-right: auto; padding: 0 1rem; text-align: center;">
        Movimente-se, cuide de você e vamos juntos nessa!
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# INFORMAÇÕES DO EVENTO
# ==============================
st.markdown("""
<div style='text-align: center; margin: 3rem 0;'>
    <div style='background: rgba(255, 20, 147, 0.2); 
                border-radius: 25px; 
                padding: 2rem;
                border: 2px solid rgba(255, 105, 180, 0.4);
                backdrop-filter: blur(15px);
                box-shadow: 0 0 60px rgba(255, 20, 147, 0.3);'>
        <h2 style='color: #ffffff; margin-bottom: 1.5rem; font-size: 2.2rem;'>
            💪 EVENTO VIP: SAÚDE & BEM-ESTAR
        </h2>
        <div style='color: rgba(255, 255, 255, 0.95); font-size: 1.2rem; line-height: 1.6; padding: 0 1rem;'>
            <div style='margin-bottom: 1rem;'>
                🏆 <span style='color: #e8919e; font-weight: 700;'>Metodologia AGYTE-SE:</span> Sistema de treino revolucionário para saúde integral
            </div>
            <div style='margin-bottom: 1rem;'>
                ❤️ <span style='color: #e8919e; font-weight: 900; text-shadow: 0 0 10px rgba(255, 20, 147, 0.8); padding: 3px 10px; border-radius: 5px;'>SAÚDE EM PRIMEIRO LUGAR:</span> Bem-estar físico e mental
            </div>
            <div>
                🎫 <span style='color: #e8919e; font-weight: 700;'>50 Convites Exclusivos:</span> Acesso antecipado
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# MENSAGEM DE DOAÇÃO DE 1KG DE ALIMENTO
# ==============================
st.markdown("""
<div class="food-donation">
    <div class="food-icon">🥫</div>
    <div class="food-title">INSCRIÇÃO SOLIDÁRIA</div>
    <div class="food-description">
    A inscrição no evento consiste na doação de <strong>1kg de alimento não perecível</strong>.<br>
    O <strong>RH informará posteriormente</strong> como e quando será feita a entrega.
</div>
</div>
""", unsafe_allow_html=True)

# ==============================
# CONTADORES PREMIUM - COM DADOS ATUALIZADOS DO BANCO
# ==============================
# CONSULTA ATUAL DO BANCO
total_banco_atual = contar_participantes()
proximo_numero_atual = obter_proximo_numero()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style='background: rgba(0, 0, 0, 0.7); 
                border-radius: 25px; 
                padding: 2rem; 
                text-align: center;
                border: 2px solid rgba(255, 105, 180, 0.5);
                backdrop-filter: blur(15px);
                box-shadow: 0 0 50px rgba(255, 20, 147, 0.4);
                height: 100%;'>
        <div style='font-size: 4rem; 
                    font-weight: 900; 
                    color: #ffffff;
                    text-shadow: 0 0 30px #ff1493;
                    margin-bottom: 0.8rem;'>
            {total_banco_atual}/50
        </div>
        <div style='color: #ffb6c1; 
                    font-size: 1.2rem; 
                    text-transform: uppercase; 
                    letter-spacing: 3px;
                    font-weight: 700;'>
            CONVITES VIP
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: rgba(0, 0, 0, 0.7); 
                border-radius: 25px; 
                padding: 2rem; 
                text-align: center;
                border: 2px solid rgba(218, 112, 214, 0.5);
                backdrop-filter: blur(15px);
                box-shadow: 0 0 50px rgba(218, 112, 214, 0.4);
                height: 100%;'>
        <div style='font-size: 3rem; color: #ffffff; margin-bottom: 1rem;'>🏃‍♀️</div>
        <div style='font-size: 2rem; color: #ffffff; font-weight: 900; margin-bottom: 0.5rem;'>
            30/01/2026
        </div>
        <div style='color: #da70d6; font-size: 1.5rem; font-weight: 700;'>
            17:50 HORAS
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='background: rgba(0, 0, 0, 0.7); 
                border-radius: 25px; 
                padding: 2rem; 
                text-align: center;
                border: 2px solid rgba(138, 43, 226, 0.5);
                backdrop-filter: blur(15px);
                box-shadow: 0 0 50px rgba(138, 43, 226, 0.4);
                height: 100%;'>
        <div style='font-size: 3rem; color: #ffffff; margin-bottom: 1rem;'>📍</div>
        <div style='font-size: 1.1rem; color: #ffffff; font-weight: 900; margin-bottom: 0.5rem; line-height: 1.4;'>
            Rua Conselheiro Galvão, 77<br>
            Maraponga/Parangaba<br>
            Fortaleza - CE
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# FORMULÁRIO PREMIUM
# ==============================
st.markdown("""
<div class="form-container">
    <h2 class="form-title">💪 GARANTA SUA INSCRIÇÃO!</h2>
    <div style='color: rgba(255, 255, 255, 0.95); text-align: center; margin-bottom: 3rem; font-weight: 600; letter-spacing: 2px; font-size: 1.2rem;'>
        ACESSO EXCLUSIVO • SAÚDE & BEM-ESTAR
    </div>
""", unsafe_allow_html=True)

# Estado da sessão para mostrar caixa
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
            help="Nome para o credenciamento VIP"
        )
    
    with col2:
        cpf_input = st.text_input(
            "CPF *",
            placeholder="000.000.000-00",
            help="Digite 11 números (somente números)",
            max_chars=14
        )
    
    setor = st.selectbox(
        "SETOR DE ATUAÇÃO *",
        [
            "💻 TI - TECNOLOGIA DA INFORMAÇÃO",
            "📊 COMERCIAL",
            "🏭 PRODUÇÃO",
            "💰 FINANCEIRO",
            "👨‍💻 TI - DESENVOLVIMENTO",
            "👔 DIRETORIA",
            "🚪 PORTARIA",
            "🧹 SERVIÇOS GERAIS",
            "🎯 MARKETING",
            "📞 ATENDIMENTO",
            "📦 LOGÍSTICA",
            "⚙️ MANUTENÇÃO",
            "🎓 RECURSOS HUMANOS",
            "📋 QUALIDADE",
            "🏢 ADMINISTRATIVO",
            "🔍 OUTROS"
        ]
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
    
    # ==============================
    # CAIXAS DE MENSAGEM ACIMA DO BOTÃO
    # ==============================
    
    # Mostrar caixa de sucesso se ativa
    if st.session_state.mostrar_caixa_sucesso:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, 
                rgba(76, 175, 80, 0.95) 0%, 
                rgba(56, 142, 60, 0.95) 100%);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            border: 3px solid rgba(255, 255, 255, 0.9);
            box-shadow: 
                0 0 60px rgba(76, 175, 80, 0.8),
                0 20px 50px rgba(0, 0, 0, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.2);
            animation: blink 1s infinite alternate;
            text-align: center;
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
        '>
            <div style='font-size: 3rem; margin-bottom: 1rem; animation: iconFloat 2s infinite ease-in-out;'>🎉</div>
            <div style='font-size: 2.2rem; font-weight: 900; color: #ffffff; margin-bottom: 1rem; text-shadow: 0 0 20px rgba(255, 255, 255, 0.8);'>
                ✅ CADASTRO CONFIRMADO!
            </div>
            <div style='font-size: 4rem; font-weight: 900; color: #ffffff; margin: 1rem 0; 
                      text-shadow: 0 0 30px rgba(255, 255, 255, 1);
                      background: linear-gradient(45deg, #ffffff, #a5d6a7);
                      -webkit-background-clip: text;
                      -webkit-text-fill-color: transparent;
                      animation: vipPulse 1.5s infinite alternate;'>
                VIP {st.session_state.numero_vip_sucesso}/50
            </div>
            <div style='font-size: 1.5rem; color: rgba(255, 255, 255, 0.95); font-weight: 700;'>
                AGYTE-SE CONFIRMADO COM SUCESSO
            </div>
        </div>
        
        <style>
        @keyframes blink {{
            0%, 100% {{ 
                opacity: 1;
                box-shadow: 0 0 60px rgba(76, 175, 80, 0.8);
            }}
            50% {{ 
                opacity: 0.9;
                box-shadow: 0 0 80px rgba(76, 175, 80, 1);
            }}
        }}
        
        @keyframes vipPulse {{
            0% {{ transform: scale(1); }}
            100% {{ transform: scale(1.05); }}
        }}
        
        @keyframes iconFloat {{
            0%, 100% {{ transform: translateY(0) rotate(0deg); }}
            50% {{ transform: translateY(-10px) rotate(5deg); }}
        }}
        </style>
        
        <script>
        // Remove a caixa após 5 segundos
        setTimeout(() => {{
            const caixa = document.querySelector('div[style*="animation: blink"]');
            if (caixa) caixa.style.display = 'none';
        }}, 5000);
        </script>
        """, unsafe_allow_html=True)
    
    # Mostrar caixa de erro se ativa
    if st.session_state.mostrar_caixa_erro:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, 
                rgba(244, 67, 54, 0.95) 0%, 
                rgba(211, 47, 47, 0.95) 100%);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            border: 3px solid rgba(255, 255, 255, 0.9);
            box-shadow: 
                0 0 60px rgba(244, 67, 54, 0.8),
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
        
        <style>
        @keyframes blinkRed {{
            0%, 100% {{ 
                opacity: 1;
                box-shadow: 0 0 60px rgba(244, 67, 54, 0.8);
            }}
            50% {{ 
                opacity: 0.9;
                box-shadow: 0 0 80px rgba(244, 67, 54, 1);
            }}
        }}
        </style>
        
        <script>
        // Remove a caixa após 4 segundos
        setTimeout(() => {{
            const caixa = document.querySelector('div[style*="animation: blinkRed"]');
            if (caixa) caixa.style.display = 'none';
        }}, 4000);
        </script>
        """, unsafe_allow_html=True)
    
    # ==============================
    # BOTÃO DE SUBMIT MELHORADO E MAIOR
    # ==============================
    col_btn = st.columns([1])
with col_btn[0]:
    submitted = st.form_submit_button(
        "👉 CLIQUE AQUI PRA FAZER SUA INSCRIÇÃO 👈",
        use_container_width=False
    )

st.markdown("""
<style>
/* Centraliza o botão */
div[data-testid="stFormSubmitButton"] {
    display: flex;
    justify-content: center;
}

/* Botão principal */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #00c853, #2e7d32);
    color: white;
    font-size: 1.1rem;
    font-weight: 800;
    padding: 0.9rem 1.6rem;
    border-radius: 50px;
    border: none;
    width: auto;              /* NÃO estica */
    min-width: 260px;
    max-width: 420px;
    box-shadow: 0 0 25px rgba(0, 200, 83, 0.6);
    animation: pulseBtn 2s infinite;
    transition: all 0.25s ease-in-out;
}

/* Hover */
div[data-testid="stFormSubmitButton"] > button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 40px rgba(0, 255, 120, 0.9);
    background: linear-gradient(135deg, #00e676, #1b5e20);
}

/* Animação pulse */
@keyframes pulseBtn {
    0% { box-shadow: 0 0 15px rgba(0, 200, 83, 0.5); }
    50% { box-shadow: 0 0 35px rgba(0, 255, 120, 0.9); }
    100% { box-shadow: 0 0 15px rgba(0, 200, 83, 0.5); }
}
</style>
""", unsafe_allow_html=True)


st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# PROCESSAMENTO DO FORMULÁRIO - COM CONSULTAS ATUALIZADAS
# ==============================
if submitted:
    # Limpar caixas anteriores
    st.session_state.mostrar_caixa_sucesso = False
    st.session_state.mostrar_caixa_erro = False
    
    # ATUALIZAR DADOS DO BANCO ANTES DE PROCESSAR
    total_banco_atual = contar_participantes()
    proximo_numero_atual = obter_proximo_numero()
    
    # Limpar e formatar dados
    nome_limpo = nome.strip().upper() if nome else ""
    cpf_limpo = formatar_cpf(cpf_input)
    telefone_limpo = formatar_telefone(telefone_input)
    
    # Validar campos vazios
    if not nome_limpo or not cpf_limpo or not telefone_limpo:
        st.session_state.mensagem_erro = "Preencha todos os campos!"
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    # Validar CPF
    elif len(cpf_limpo) != 11:
        st.session_state.mensagem_erro = f"CPF deve ter 11 números! Você digitou {len(cpf_limpo)}."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    # Validar telefone
    elif len(telefone_limpo) < 10:
        st.session_state.mensagem_erro = f"Telefone deve ter pelo menos 10 números! Você digitou {len(telefone_limpo)}."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    # Verificar limite - USANDO DADOS ATUALIZADOS
    elif total_banco_atual >= 50:
        st.session_state.mensagem_erro = "EVENTO ESGOTADO! Todas as 50 vagas já foram preenchidas."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    # Verificar CPF duplicado - CONSULTA ATUALIZADA
    elif verificar_cpf_existente(cpf_limpo):
        st.session_state.mensagem_erro = "Este CPF já está cadastrado!"
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    # Tentar cadastrar
    else:
        setor_formatado = setor.split("-")[0].strip() if "-" in setor else setor.split(" ")[0]
        unidade_formatada = unidade.replace("🏢", "").replace("💖", "").replace("❤️", "").strip()
        
        success, message = inserir_participante(
            nome=nome_limpo,
            cpf=cpf_limpo,
            setor=setor_formatado,
            unidade=unidade_formatada,
            telefone=telefone_limpo,
            numero_vip=proximo_numero_atual,  # USA NÚMERO ATUALIZADO
            evento="FUNCIONAL"
        )
        
        if success:
            st.session_state.numero_vip_sucesso = proximo_numero_atual
            st.session_state.mostrar_caixa_sucesso = True
            
            # Efeito visual de vibração
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
# CONTADOR DE VAGAS - SEMPRE ATUALIZADO
# ==============================
# CONSULTA FINAL DO BANCO
total_final = contar_participantes()
vagas_restantes = 50 - total_final if total_final < 50 else 0

st.markdown(f"""
<div class="counter-container" style='text-align: center; padding: 1.5rem; 
            background: linear-gradient(135deg, rgba(255, 20, 147, 0.3), rgba(218, 112, 214, 0.3));
            border-radius: 20px; 
            border: 2px solid rgba(255, 255, 255, 0.4);
            margin-top: 1rem !important;'>
    <div style='font-size: 3.5rem; font-weight: 900; 
                background: linear-gradient(45deg, #ffffff, #ffb6c1, #ffffff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
                text-shadow: 0 0 40px rgba(255, 20, 147, 0.6);'>
        {total_final}/50
    </div>
    <div style='color: #ffffff; 
                font-weight: 800; 
                letter-spacing: 3px;
                text-transform: uppercase;
                font-size: 1.2rem;
                margin-bottom: 0.8rem;'>
        CONVITES CONFIRMADOS
    </div>
""", unsafe_allow_html=True)

if total_final >= 50:
    st.markdown(f"""
    <div style='color: #ff1493; 
                font-size: 1.1rem; 
                font-weight: 900;
                background: rgba(0, 0, 0, 0.4);
                padding: 0.8rem 1.5rem;
                border-radius: 12px;
                display: inline-block;
                box-shadow: 0 0 15px rgba(255, 20, 147, 0.3);
                animation: pulse 2s infinite;'>
        🚫 EVENTO ESGOTADO • {total_final}/50
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style='color: #ffb6c1; 
                font-size: 1rem; 
                font-weight: 700;
                background: rgba(0, 0, 0, 0.4);
                padding: 0.8rem 1.5rem;
                border-radius: 12px;
                display: inline-block;
                box-shadow: 0 0 15px rgba(255, 20, 147, 0.3);'>
        {vagas_restantes} VAGAS VIP RESTANTES
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# RODAPÉ
# ==============================
st.markdown("""
<div class="footer-container" style="text-align: center; padding: 2rem 1rem; margin-top: 1.5rem !important; 
            border-top: 2px solid rgba(255, 105, 180, 0.5);
            background: rgba(0, 0, 0, 0.5);
            border-radius: 0 0 30px 30px;">
    <div style="font-size: 3rem; font-weight: 900; 
                background: linear-gradient(45deg, #ff1493, #da70d6, #ff1493);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1rem;
                text-shadow: 0 0 40px rgba(255, 20, 147, 0.7);">
        AGYTE-SE
    </div>
    <div style="color: rgba(255, 255, 255, 0.95); margin-bottom: 0.8rem; font-size: 1.4rem; font-weight: 700;">
        TREINO FUNCIONAL PREMIUM • SAÚDE & BEM-ESTAR
    </div>
    <div style="color: rgba(255, 255, 255, 0.85); font-size: 1rem; letter-spacing: 2px; margin-bottom: 0.5rem;">
        📍 Rua Conselheiro Galvão, 77 - Maraponga/Parangaba - Fortaleza/CE
    </div>
    <div style="color: rgba(255, 255, 255, 0.75); font-size: 0.9rem; letter-spacing: 1px;">
        30 DE JANEIRO 2026 • 17:50H • CONVITES LIMITADOS
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

