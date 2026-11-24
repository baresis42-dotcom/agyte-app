import streamlit as st
from datetime import datetime
import time
import random
from streamlit.components.v1 import html
import psycopg2
from psycopg2.extras import RealDictCursor
import os

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

def inserir_participante(nome, cpf, setor, unidade, telefone, numero_vip, evento="FUNCIONAL"):
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
    """Conta o total de participantes no banco"""
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
    """Verifica se CPF já está cadastrado no banco"""
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
        print(f"Erro ao verificar CPF: {e}")
        return False

def obter_proximo_numero():
    """Obtém o próximo número VIP baseado no banco"""
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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="AULÃO FUNCIONAL",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS CUSTOMIZADO (CORRIGIDO E MAIS BONITO) ---
st.markdown("""
<style>
    /* FUNDO DINÂMICO - ROSA/ROXO/LARANJA */
    .stApp {
        background: linear-gradient(-45deg, #ff0080, #ff8c00, #7b2cbf, #ff0080);
        background-size: 400% 400%;
        animation: gradientBG 12s ease infinite;
        min-height: 100vh;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* EFEITO DE VIDRO */
    .glass-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 25px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        padding: 2rem;
        margin: 1.5rem auto;
        max-width: 900px;
        color: white;
        text-align: center;
    }

    /* TÍTULOS */
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 4px;
        line-height: 1.1;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(255, 0, 128, 0.8);
    }

    .sub-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #fff;
        letter-spacing: 2px;
        margin-bottom: 2rem;
        text-transform: uppercase;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }

    /* BADGES */
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .info-badge {
        background: rgba(0, 0, 0, 0.4);
        border: 2px solid #ff0080;
        padding: 10px 20px;
        border-radius: 50px;
        font-size: 1rem;
        font-weight: 700;
        box-shadow: 0 0 15px rgba(255, 0, 128, 0.5);
        color: white;
    }

    /* CARDS */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
    }

    .stat-number {
        font-size: 2.5rem;
        font-weight: 900;
        color: #fff;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }

    .stat-label {
        font-size: 0.9rem;
        font-weight: 700;
        color: #ffcc00;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }

    /* FORMULÁRIO */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(0, 0, 0, 0.4) !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 10px !important;
    }

    .stTextInput label,
    .stSelectbox label {
        color: white !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    /* BOTÃO */
    .stButton button {
        background: linear-gradient(45deg, #ff0080, #ff8c00);
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 1rem 2rem !important;
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        width: 100% !important;
        box-shadow: 0 0 20px rgba(255, 0, 128, 0.8);
        transition: all 0.3s ease !important;
    }

    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 40px rgba(255, 140, 0, 1);
    }

    /* CAIXAS DE MENSAGEM */
    .success-box {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        text-align: center;
    }

    .error-box {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        text-align: center;
    }
    
    /* ESCONDER MENU STREAMLIT */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- CONTEÚDO PRINCIPAL ---
st.markdown("""
<div class="glass-container">
    <div style="text-align: center;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🔥</div>
        <h1 class="main-title">AULÃO<br>FUNCIONAL</h1>
        <div class="sub-title">VAMOS CONTINUAR O MOVIMENTO!</div>
    </div>
    
    <div class="badge-container">
        <div class="info-badge">📅 05 DE DEZEMBRO</div>
        <div class="info-badge">⏰ 05:45</div>
        <div class="info-badge">📍 BEIRA MAR</div>
    </div>

    <div style="background: rgba(0,0,0,0.3); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border-left: 5px solid #ff0080; text-align: left;">
        <p style="font-size: 1.1rem; margin: 0; color: #fff;">
            <strong>Local:</strong> Av. Beira Mar, nº 2340 - Meireles, Fortaleza - CE<br>
            <small>(Em frente ao Hotel Bourbon)</small>
        </p>
    </div>

    <div class="card-grid">
        <div class="stat-card">
            <div class="stat-number">50</div>
            <div class="stat-label">Vagas Totais</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">R$ 10</div>
            <div class="stat-label">Taxa Social</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">+1</div>
            <div class="stat-label">Dependente</div>
        </div>
    </div>
    
    <p style="font-size: 0.9rem; color: #ffcc00; font-weight: bold; text-transform: uppercase;">
        ⚠️ Taxa revertida para instituições carentes
    </p>
</div>
""", unsafe_allow_html=True)

# --- LÓGICA DE DADOS ---
total_banco_atual = contar_participantes()
proximo_numero_atual = obter_proximo_numero()
vagas_restantes = 50 - total_banco_atual # Ajustado para 50

# --- FORMULÁRIO DE INSCRIÇÃO ---
st.markdown("""
<div class="glass-container" style="margin-top: -1rem;">
    <h2 style="color: #fff; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1.5rem;">
        GARANTA SUA VAGA
    </h2>
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
        nome = st.text_input("NOME COMPLETO *", placeholder="Seu nome aqui")
        setor = st.text_input("SETOR DE ATUAÇÃO", placeholder="Ex: TI, Comercial... (opcional)")
        telefone_input = st.text_input("WHATSAPP *", placeholder="(85) 99999-9999", max_chars=15)
    
    with col2:
        cpf_input = st.text_input("CPF *", placeholder="000.000.000-00", max_chars=14)
        unidade = st.selectbox("UNIDADE *", ["🏢 DILADY", "💖 FINNA", "❤️ LOVE"])
        # Espaço vazio para alinhar o botão visualmente se necessário
    
    if st.session_state.mostrar_caixa_sucesso:
        st.markdown(f"""
        <div class="success-box">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎉</div>
            <h3 style="margin: 0; font-size: 1.5rem;">INSCRIÇÃO CONFIRMADA!</h3>
            <div style="font-size: 2.5rem; font-weight: 900; margin: 1rem 0;">Nº {st.session_state.numero_vip_sucesso}</div>
            <p style="font-size: 1rem;">Nos vemos no Aulão! 💪</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.mostrar_caixa_erro:
        st.markdown(f"""
        <div class="error-box">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⚠️</div>
            <h3 style="margin: 0; font-size: 1.2rem;">{st.session_state.mensagem_erro}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    submitted = st.form_submit_button("🔥 QUERO MINHA VAGA AGORA! 🔥", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- PROCESSAMENTO ---
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
        st.session_state.mensagem_erro = "CPF inválido! Digite 11 números."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    elif len(telefone_limpo) < 10:
        st.session_state.mensagem_erro = "Telefone inválido! Digite com DDD."
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    elif total_banco_atual >= 50: # Ajustado para 50
        st.session_state.mensagem_erro = "VAGAS ESGOTADAS! 😭"
        st.session_state.mostrar_caixa_erro = True
        st.rerun()
    
    elif verificar_cpf_existente(cpf_limpo):
        st.session_state.mensagem_erro = "Este CPF já está cadastrado!"
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
            evento="FUNCIONAL"
        )
        
        if success:
            st.session_state.numero_vip_sucesso = proximo_numero_atual
            st.session_state.mostrar_caixa_sucesso = True
        else:
            st.session_state.mensagem_erro = f"Erro: {message}"
            st.session_state.mostrar_caixa_erro = True
    
    st.rerun()

# --- CONTADOR FINAL E RODAPÉ ---
total_final = contar_participantes()
vagas_restantes = 50 - total_final if total_final < 50 else 0 # Ajustado para 50

st.markdown(f"""
<div class="glass-container" style="text-align: center;">
    <div style="font-size: 3rem; font-weight: 900; color: #fff; text-shadow: 0 0 20px rgba(255,0,128,0.8);">
        {total_final}/50
    </div>
    <div style="color: #ffcc00; font-weight: 700; letter-spacing: 3px; text-transform: uppercase;">
        INSCRITOS
    </div>
    <div style="margin-top: 1rem; color: #fff; font-size: 1.1rem;">
        {'🚫 VAGAS ESGOTADAS' if total_final >= 50 else f'🔥 Apenas {vagas_restantes} vagas restantes!'}
    </div>
</div>

<div style="text-align: center; color: rgba(255,255,255,0.7); padding: 2rem; font-size: 0.8rem;">
    <p>AULÃO FUNCIONAL • 05/DEZ • 05:45 • BEIRA MAR</p>
</div>
""", unsafe_allow_html=True)
