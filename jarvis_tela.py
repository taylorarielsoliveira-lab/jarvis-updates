import tkinter as tk
import threading
import ctypes
import math
import time
import os
import re
import unicodedata
import sqlite3
import asyncio
import shutil
import sys

import cv2
import mediapipe as mp
import speech_recognition as sr
import edge_tts
import pygame
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

try:
    from google import genai
except ImportError:
    genai = None


# ============================================================
# PASTA PRINCIPAL
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# ATUALIZAÇÃO AUTOMÁTICA
# ============================================================

ARQUIVO_PRINCIPAL = os.path.join(
    BASE_DIR,
    "jarvis_tela.py"
)

ARQUIVO_VERSAO = os.path.join(
    BASE_DIR,
    "jarvis_version.txt"
)

ARQUIVO_BACKUP = os.path.join(
    BASE_DIR,
    "jarvis_tela_backup.py"
)

URL_VERSAO = (
    "https://raw.githubusercontent.com/"
    "taylorarielsoliveira-lab/"
    "jarvis-updates/main/version.txt"
)

URL_ATUALIZACAO = (
    "https://raw.githubusercontent.com/"
    "taylorarielsoliveira-lab/"
    "jarvis-updates/main/jarvis_tela.py"
)


def converter_versao(versao):
    try:
        return tuple(
            int(parte)
            for parte in versao.strip().split(".")
        )
    except Exception:
        return (0,)


def obter_versao_local():
    if not os.path.exists(ARQUIVO_VERSAO):
        with open(
            ARQUIVO_VERSAO,
            "w",
            encoding="utf-8"
        ) as arquivo:
            arquivo.write("0.2")

        return "0.2"

    try:
        with open(
            ARQUIVO_VERSAO,
            "r",
            encoding="utf-8"
        ) as arquivo:
            return arquivo.read().strip()

    except Exception:
        return "0.2"


def salvar_versao_local(versao):
    with open(
        ARQUIVO_VERSAO,
        "w",
        encoding="utf-8"
    ) as arquivo:
        arquivo.write(versao)


def validar_codigo_atualizacao(codigo):
    if len(codigo) < 1000:
        print(
            "Atualização ignorada: "
            "arquivo remoto muito pequeno."
        )
        return False

    itens_obrigatorios = [
        "J.A.R.V.I.S",
        "def responder",
        "def sistema_de_voz",
        "def desenhar_hud",
        "def verificar_atualizacao_automatica"
    ]

    for item in itens_obrigatorios:
        if item not in codigo:
            print(
                "Atualização recusada. "
                "Componente ausente:",
                item
            )
            return False

    try:
        compile(
            codigo,
            "jarvis_tela.py",
            "exec"
        )

    except SyntaxError as erro:
        print(
            "Atualização com erro de sintaxe:",
            erro
        )
        return False

    return True


def verificar_atualizacao_automatica():
    try:
        versao_local = obter_versao_local()

        print("")
        print("==============================")
        print("   J.A.R.V.I.S. UPDATE")
        print("==============================")
        print("")
        print(
            "Versão instalada:",
            versao_local
        )
        print(
            "Verificando atualizações..."
        )

        resposta_versao = requests.get(
            URL_VERSAO,
            timeout=8
        )

        resposta_versao.raise_for_status()

        versao_remota = resposta_versao.text.strip()

        print(
            "Versão disponível:",
            versao_remota
        )

        if (
            converter_versao(versao_remota)
            <= converter_versao(versao_local)
        ):
            print(
                "J.A.R.V.I.S. já está atualizado."
            )
            print("")
            return False

        print("")
        print("Nova versão encontrada.")
        print(
            versao_local,
            "->",
            versao_remota
        )
        print("")
        print(
            "Baixando atualização..."
        )

        resposta_codigo = requests.get(
            URL_ATUALIZACAO,
            timeout=20
        )

        resposta_codigo.raise_for_status()

        codigo_novo = resposta_codigo.text

        print(
            "Validando atualização..."
        )

        if not validar_codigo_atualizacao(
            codigo_novo
        ):
            print(
                "Atualização cancelada."
            )
            return False

        print(
            "Criando backup..."
        )

        if os.path.exists(
            ARQUIVO_PRINCIPAL
        ):
            shutil.copy2(
                ARQUIVO_PRINCIPAL,
                ARQUIVO_BACKUP
            )

        temporario = os.path.join(
            BASE_DIR,
            "jarvis_tela_novo.py"
        )

        try:
            with open(
                temporario,
                "w",
                encoding="utf-8"
            ) as arquivo:
                arquivo.write(
                    codigo_novo
                )

            with open(
                temporario,
                "r",
                encoding="utf-8"
            ) as arquivo:
                teste = arquivo.read()

            compile(
                teste,
                temporario,
                "exec"
            )

            os.replace(
                temporario,
                ARQUIVO_PRINCIPAL
            )

            salvar_versao_local(
                versao_remota
            )

            print("")
            print(
                "ATUALIZAÇÃO CONCLUÍDA"
            )
            print(
                "Nova versão:",
                versao_remota
            )
            print("")
            print(
                "Reiniciando J.A.R.V.I.S..."
            )

            time.sleep(1)

            os.execv(
                sys.executable,
                [
                    sys.executable,
                    ARQUIVO_PRINCIPAL
                ]
            )

        except Exception as erro:
            print(
                "Falha ao instalar atualização:",
                erro
            )

            if os.path.exists(
                ARQUIVO_BACKUP
            ):
                print(
                    "Restaurando backup..."
                )

                shutil.copy2(
                    ARQUIVO_BACKUP,
                    ARQUIVO_PRINCIPAL
                )

            if os.path.exists(
                temporario
            ):
                try:
                    os.remove(
                        temporario
                    )
                except Exception:
                    pass

            return False

    except Exception as erro:
        print(
            "Não foi possível verificar "
            "atualizações."
        )
        print(
            "Continuando com a versão instalada."
        )
        print(
            "Detalhes:",
            erro
        )
        print("")

    return False


# ============================================================
# VERIFICA UPDATE ANTES DE ABRIR
# ============================================================

verificar_atualizacao_automatica()


# ============================================================
# CONFIGURAÇÕES
# ============================================================

CIDADE_PADRAO = "Pará de Minas"

MODELO_GEMINI = "gemini-3.5-flash-lite"

ARQUIVO_MEMORIA = os.path.join(
    BASE_DIR,
    "jarvis_memoria.db"
)

COR_FUNDO = "#020609"
COR_CIANO = "#00E5FF"
COR_CIANO_ESCURO = "#006A78"
COR_TEXTO = "#BDF7FF"

sistema_rodando = True
modo_ativo = False

status_voz = "ESPERA"
status_camera = "INICIANDO"
status_mao = "INICIANDO"
status_ia = "ONLINE"

ultima_fala = "À disposição senhor"


# ============================================================
# GEMINI
# ============================================================

cliente_gemini = None

if genai is not None:
    try:
        if os.getenv(
            "GEMINI_API_KEY"
        ):
            cliente_gemini = genai.Client()
        else:
            status_ia = "SEM CHAVE"

    except Exception as erro:
        print(
            "Erro ao iniciar Gemini:",
            erro
        )

        status_ia = "ERRO"

else:
    status_ia = "INDISPONÍVEL"


# ============================================================
# VOZ
# ============================================================

reconhecedor = sr.Recognizer()

microfone = sr.Microphone()

palavras_ativacao = [
    "jarvis",
    "javis",
    "jarves",
    "jarvi",
    "drive",
    "jackson",
    "chave",
    "chaves"
]

comandos_dormir = [
    "pode descansar",
    "pode dormir",
    "modo de espera",
    "entrar em espera",
    "voltar para espera",
    "descanse",
    "dormir jarvis",
    "jarvis dormir"
]


# ============================================================
# PAÍSES
# ============================================================

paises = {
    "japao": "Tokyo",
    "brasil": "Brasilia",
    "estados unidos": "Washington",
    "eua": "Washington",
    "argentina": "Buenos Aires",
    "uruguai": "Montevideo",
    "paraguai": "Asuncion",
    "chile": "Santiago",
    "peru": "Lima",
    "colombia": "Bogota",
    "venezuela": "Caracas",
    "mexico": "Mexico City",
    "canada": "Ottawa",
    "portugal": "Lisbon",
    "espanha": "Madrid",
    "franca": "Paris",
    "italia": "Rome",
    "alemanha": "Berlin",
    "reino unido": "London",
    "inglaterra": "London",
    "irlanda": "Dublin",
    "suica": "Zurich",
    "austria": "Vienna",
    "belgica": "Brussels",
    "holanda": "Amsterdam",
    "paises baixos": "Amsterdam",
    "noruega": "Oslo",
    "suecia": "Stockholm",
    "finlandia": "Helsinki",
    "dinamarca": "Copenhagen",
    "polonia": "Warsaw",
    "grecia": "Athens",
    "turquia": "Istanbul",
    "russia": "Moscow",
    "ucrania": "Kyiv",
    "china": "Beijing",
    "india": "New Delhi",
    "coreia do sul": "Seoul",
    "coreia": "Seoul",
    "tailandia": "Bangkok",
    "singapura": "Singapore",
    "indonesia": "Jakarta",
    "australia": "Canberra",
    "nova zelandia": "Wellington",
    "africa do sul": "Pretoria",
    "egito": "Cairo",
    "marrocos": "Rabat",
    "emirados arabes": "Dubai",
    "emirados arabes unidos": "Dubai",
    "arabia saudita": "Riyadh",
    "israel": "Jerusalem"
}


# ============================================================
# TEXTO
# ============================================================

def normalizar(texto):
    texto = texto.lower().strip()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(
            caractere
        ) != "Mn"
    )

    return texto


def limpar_texto_para_voz(texto):
    if not texto:
        return ""

    texto = re.sub(
        r"```.*?```",
        "",
        texto,
        flags=re.DOTALL
    )

    texto = texto.replace(
        "**",
        ""
    )

    texto = texto.replace(
        "__",
        ""
    )

    texto = texto.replace(
        "*",
        ""
    )

    texto = texto.replace(
        "#",
        ""
    )

    texto = texto.replace(
        "`",
        ""
    )

    texto = texto.replace(
        ">",
        ""
    )

    texto = texto.replace(
        "_",
        " "
    )

    texto = re.sub(
        r"(?m)^\s*[-•]\s*",
        "",
        texto
    )

    texto = re.sub(
        r"(?m)^\s*\d+\.\s*",
        "",
        texto
    )

    texto = re.sub(
        r"\n+",
        ". ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# MEMÓRIA
# ============================================================

def conectar_memoria():
    return sqlite3.connect(
        ARQUIVO_MEMORIA
    )


def criar_banco_memoria():
    conexao = conectar_memoria()

    cursor = conexao.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conteudo TEXT NOT NULL,
            criado_em TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            jarvis TEXT NOT NULL,
            criado_em TEXT NOT NULL
        )
        """
    )

    conexao.commit()
    conexao.close()


def salvar_memoria(conteudo):
    conexao = conectar_memoria()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO memorias (
            conteudo,
            criado_em
        )
        VALUES (?, ?)
        """,
        (
            conteudo,
            datetime.now().isoformat()
        )
    )

    conexao.commit()
    conexao.close()


def listar_memorias(limite=15):
    conexao = conectar_memoria()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT conteudo
        FROM memorias
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            limite,
        )
    )

    resultado = cursor.fetchall()

    conexao.close()

    return [
        item[0]
        for item in resultado
    ]


def apagar_memorias(termo):
    conexao = conectar_memoria()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT id
        FROM memorias
        WHERE conteudo LIKE ?
        """,
        (
            f"%{termo}%",
        )
    )

    resultados = cursor.fetchall()

    for resultado in resultados:
        cursor.execute(
            """
            DELETE FROM memorias
            WHERE id = ?
            """,
            (
                resultado[0],
            )
        )

    conexao.commit()
    conexao.close()

    return len(resultados)


def salvar_conversa(
    usuario,
    jarvis
):
    conexao = conectar_memoria()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO conversas (
            usuario,
            jarvis,
            criado_em
        )
        VALUES (?, ?, ?)
        """,
        (
            usuario,
            jarvis,
            datetime.now().isoformat()
        )
    )

    conexao.commit()

    cursor.execute(
        """
        DELETE FROM conversas
        WHERE id NOT IN (
            SELECT id
            FROM conversas
            ORDER BY id DESC
            LIMIT 100
        )
        """
    )

    conexao.commit()
    conexao.close()


def historico_recente(limite=5):
    conexao = conectar_memoria()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT usuario, jarvis
        FROM conversas
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            limite,
        )
    )

    resultados = cursor.fetchall()

    conexao.close()

    resultados.reverse()

    return resultados


# ============================================================
# VOZ DO JARVIS
# ============================================================

async def falar_async(texto):
    arquivo = os.path.join(
        BASE_DIR,
        "resposta_jarvis.mp3"
    )

    texto = limpar_texto_para_voz(
        texto
    )

    try:
        voz = edge_tts.Communicate(
            texto,
            "pt-BR-AntonioNeural",
            rate="-8%",
            pitch="-6Hz",
            volume="+0%"
        )

        await voz.save(
            arquivo
        )

        pygame.mixer.init()

        pygame.mixer.music.load(
            arquivo
        )

        pygame.mixer.music.play()

        while (
            pygame.mixer.music.get_busy()
            and sistema_rodando
        ):
            pygame.time.Clock().tick(
                10
            )

        pygame.mixer.music.stop()
        pygame.mixer.quit()

    except Exception as erro:
        print(
            "Erro na voz:",
            erro
        )

    finally:
        if os.path.exists(
            arquivo
        ):
            try:
                os.remove(
                    arquivo
                )
            except Exception:
                pass


def falar(texto):
    global status_voz
    global ultima_fala

    ultima_fala = texto

    status_voz = "FALANDO"

    try:
        asyncio.run(
            falar_async(
                texto
            )
        )

    finally:
        if modo_ativo:
            status_voz = "CONVERSA"
        else:
            status_voz = "ESPERA"


# ============================================================
# INTERNET
# ============================================================

def requisicao_segura(
    url,
    parametros,
    tentativas=3
):
    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):
        try:
            resposta = requests.get(
                url,
                params=parametros,
                timeout=20
            )

            resposta.raise_for_status()

            return resposta

        except requests.exceptions.RequestException as erro:
            ultimo_erro = erro

            if tentativa < tentativas:
                time.sleep(1)

    raise ultimo_erro


# ============================================================
# LOCALIZAÇÃO
# ============================================================

def descobrir_local(pergunta):
    texto = normalizar(
        pergunta
    )

    for pais, cidade in paises.items():
        if pais in texto:
            return cidade

    padroes = [
        r"\bem\s+(.+)",
        r"\bdo\s+(.+)",
        r"\bda\s+(.+)",
        r"\bde\s+(.+)"
    ]

    cortes = [
        " e vai",
        " e qual",
        " e como",
        " hoje",
        " amanha",
        " agora",
        " vai chover",
        " temperatura",
        " porcentagem",
        " chance",
        " previsao",
        " clima",
        " tempo"
    ]

    for padrao in padroes:
        resultado = re.search(
            padrao,
            texto
        )

        if resultado:
            local = resultado.group(
                1
            ).strip()

            for corte in cortes:
                if corte in local:
                    local = local.split(
                        corte
                    )[0].strip()

            local = local.strip(
                " ?,.!"
            )

            if local:
                return local

    return CIDADE_PADRAO


def buscar_localizacao(nome):
    resposta = requisicao_segura(
        "https://geocoding-api.open-meteo.com/v1/search",
        {
            "name": nome,
            "count": 5,
            "language": "pt",
            "format": "json"
        }
    )

    dados = resposta.json()

    resultados = dados.get(
        "results",
        []
    )

    if not resultados:
        return None

    local = resultados[0]

    return {
        "nome": local.get(
            "name",
            nome
        ),
        "pais": local.get(
            "country",
            ""
        ),
        "latitude": local[
            "latitude"
        ],
        "longitude": local[
            "longitude"
        ],
        "timezone": local[
            "timezone"
        ]
    }


# ============================================================
# HORÁRIO
# ============================================================

def horario_natural(data_hora):
    hora24 = data_hora.hour
    minuto = data_hora.minute

    if (
        hora24 == 0
        and minuto == 0
    ):
        return "meia-noite"

    if (
        hora24 == 12
        and minuto == 0
    ):
        return "meio-dia"

    hora12 = hora24 % 12

    if hora12 == 0:
        hora12 = 12

    if minuto == 0:
        if hora12 == 1:
            return "1 hora"

        return f"{hora12} horas"

    if hora12 == 1:
        return (
            f"1 hora e "
            f"{minuto} minutos"
        )

    return (
        f"{hora12} horas e "
        f"{minuto} minutos"
    )


# ============================================================
# DATA
# ============================================================

def data_natural(data):
    meses = [
        "",
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro"
    ]

    dias = [
        "segunda-feira",
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "sábado",
        "domingo"
    ]

    return (
        f"{dias[data.weekday()]}, "
        f"dia {data.day} de "
        f"{meses[data.month]} de "
        f"{data.year}"
    )


# ============================================================
# CLIMA
# ============================================================

def buscar_clima(local):
    resposta = requisicao_segura(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": local[
                "latitude"
            ],
            "longitude": local[
                "longitude"
            ],
            "current":
                "temperature_2m,"
                "apparent_temperature,"
                "weather_code",
            "daily":
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "weather_code",
            "forecast_days": 3,
            "timezone": local[
                "timezone"
            ]
        }
    )

    return resposta.json()


def descricao_tempo(codigo):
    descricoes = {
        0: "com céu limpo",
        1: "predominantemente limpo",
        2: "parcialmente nublado",
        3: "nublado",
        45: "com neblina",
        48: "com neblina",
        51: "com garoa leve",
        53: "com garoa",
        55: "com garoa forte",
        61: "com chuva leve",
        63: "com chuva moderada",
        65: "com chuva forte",
        71: "com neve leve",
        73: "com neve",
        75: "com neve forte",
        80: "com pancadas leves de chuva",
        81: "com pancadas de chuva",
        82: "com pancadas fortes de chuva",
        95: "com tempestades",
        96: "com tempestades e granizo",
        99: "com tempestades fortes e granizo"
    }

    return descricoes.get(
        codigo,
        "com condições variadas"
    )


def pergunta_local(texto):
    termos = [
        "que horas",
        "qual o horario",
        "qual horario",
        "horario em",
        "hora agora",
        "quantas horas",
        "qual a hora",
        "que dia e hoje",
        "qual a data",
        "data de hoje",
        "dia da semana",
        "previsao do tempo",
        "como esta o tempo",
        "como vai estar o tempo",
        "como esta o clima",
        "clima hoje",
        "clima amanha",
        "temperatura",
        "quantos graus",
        "vai chover",
        "chance de chuva",
        "porcentagem de chuva"
    ]

    return any(
        termo in texto
        for termo in termos
    )


def responder_local(pergunta):
    texto = normalizar(
        pergunta
    )

    try:
        cidade = descobrir_local(
            pergunta
        )

        local = buscar_localizacao(
            cidade
        )

        if not local:
            return (
                f"Senhor, não consegui "
                f"localizar {cidade}."
            )

        agora = datetime.now(
            ZoneInfo(
                local[
                    "timezone"
                ]
            )
        )

        tem_amanha = (
            "amanha" in texto
        )

        tem_hoje = (
            "hoje" in texto
        )

        nome_local = local[
            "nome"
        ]

        if local["pais"]:
            nome_local += (
                f", {local['pais']}"
            )

        partes = []

        quer_hora = any(
            termo in texto
            for termo in [
                "que horas",
                "qual o horario",
                "qual horario",
                "horario em",
                "hora agora",
                "quantas horas",
                "qual a hora"
            ]
        )

        quer_data = any(
            termo in texto
            for termo in [
                "que dia e hoje",
                "qual a data",
                "data de hoje",
                "dia da semana"
            ]
        )

        quer_clima = any(
            termo in texto
            for termo in [
                "previsao do tempo",
                "como esta o tempo",
                "como vai estar o tempo",
                "como esta o clima",
                "clima hoje",
                "clima amanha",
                "temperatura",
                "quantos graus",
                "vai chover",
                "chance de chuva",
                "porcentagem de chuva"
            ]
        )

        if quer_hora:
            partes.append(
                f"em {nome_local}, "
                f"agora são "
                f"{horario_natural(agora)}"
            )

        if quer_data:
            data = agora

            if tem_amanha:
                data += timedelta(
                    days=1
                )

            partes.append(
                f"a data é "
                f"{data_natural(data)}"
            )

        if quer_clima:
            clima = buscar_clima(
                local
            )

            diaria = clima[
                "daily"
            ]

            if (
                tem_hoje
                and tem_amanha
            ):
                chuva_hoje = diaria[
                    "precipitation_probability_max"
                ][0]

                chuva_amanha = diaria[
                    "precipitation_probability_max"
                ][1]

                partes.append(
                    f"hoje a chance máxima "
                    f"de chuva é de "
                    f"{chuva_hoje} por cento"
                )

                partes.append(
                    f"amanhã a chance máxima "
                    f"de chuva é de "
                    f"{chuva_amanha} por cento"
                )

            else:
                indice = (
                    1
                    if tem_amanha
                    else 0
                )

                dia_texto = (
                    "amanhã"
                    if tem_amanha
                    else "hoje"
                )

                minima = round(
                    diaria[
                        "temperature_2m_min"
                    ][indice]
                )

                maxima = round(
                    diaria[
                        "temperature_2m_max"
                    ][indice]
                )

                chuva = diaria[
                    "precipitation_probability_max"
                ][indice]

                codigo = diaria[
                    "weather_code"
                ][indice]

                descricao = descricao_tempo(
                    codigo
                )

                partes.append(
                    f"{dia_texto} o tempo "
                    f"estará {descricao}, "
                    f"com mínima de "
                    f"{minima} graus "
                    f"e máxima de "
                    f"{maxima} graus"
                )

                partes.append(
                    f"a chance máxima de "
                    f"chuva {dia_texto} "
                    f"é de {chuva} por cento"
                )

        if not partes:
            return (
                "Senhor, não consegui "
                "identificar a informação solicitada."
            )

        return (
            "Senhor, "
            + ". ".join(
                partes
            )
            + "."
        )

    except Exception as erro:
        print(
            "ERRO LOCAL:",
            erro
        )

        return (
            "Senhor, não consegui "
            "acessar essas informações agora."
        )


# ============================================================
# COMANDOS DE MEMÓRIA
# ============================================================

def comando_memoria(pergunta):
    texto = normalizar(
        pergunta
    )

    prefixos_salvar = [
        "lembre que ",
        "lembra que ",
        "guarde que ",
        "guarda que ",
        "salve que ",
        "anote que "
    ]

    for prefixo in prefixos_salvar:
        if texto.startswith(
            prefixo
        ):
            conteudo = pergunta[
                len(prefixo):
            ].strip()

            salvar_memoria(
                conteudo
            )

            return (
                True,
                f"Certo senhor. "
                f"Vou lembrar que "
                f"{conteudo}."
            )

    prefixos_apagar = [
        "esqueca que ",
        "esquece que ",
        "apague da memoria ",
        "apagar da memoria "
    ]

    for prefixo in prefixos_apagar:
        if texto.startswith(
            prefixo
        ):
            termo = texto[
                len(prefixo):
            ].strip()

            quantidade = apagar_memorias(
                termo
            )

            if quantidade > 0:
                return (
                    True,
                    "Certo senhor. "
                    "Removi essa informação da memória."
                )

            return (
                True,
                "Senhor, não encontrei "
                "essa informação na memória."
            )

    perguntas_memoria = [
        "o que voce lembra sobre mim",
        "o que voce lembra de mim",
        "o que sabe sobre mim",
        "quais sao suas memorias",
        "mostre suas memorias",
        "me diga o que voce lembra"
    ]

    if any(
        frase in texto
        for frase in perguntas_memoria
    ):
        memorias = listar_memorias(
            10
        )

        if not memorias:
            return (
                True,
                "Senhor, ainda não tenho "
                "memórias permanentes salvas."
            )

        return (
            True,
            "Senhor, eu lembro que "
            + ". Também lembro que ".join(
                memorias
            )
            + "."
        )

    return (
        False,
        None
    )


# ============================================================
# CONTEXTO PARA IA
# ============================================================

def contexto_memoria():
    memorias = listar_memorias(
        12
    )

    if not memorias:
        return (
            "Nenhuma memória salva."
        )

    return "\n".join(
        memorias
    )


def contexto_conversa():
    conversas = historico_recente(
        4
    )

    if not conversas:
        return (
            "Sem conversa recente."
        )

    partes = []

    for usuario, resposta in conversas:
        partes.append(
            f"Senhor: {usuario}"
        )

        partes.append(
            f"JARVIS: {resposta}"
        )

    return "\n".join(
        partes
    )


# ============================================================
# GEMINI
# ============================================================

def responder_gemini(pergunta):
    global status_ia

    if cliente_gemini is None:
        return (
            "Senhor, a inteligência "
            "artificial não está disponível."
        )

    try:
        status_ia = "PENSANDO"

        prompt = f"""
Você é J.A.R.V.I.S., um assistente pessoal por voz.

Responda sempre em português do Brasil.
Sempre trate o usuário como senhor.

Seja natural, direto, inteligente e útil.

A resposta será falada em voz alta.

Não use Markdown.
Não use asteriscos.
Não use hashtags.
Não use tabelas.
Não use emojis.
Não use listas longas.

Para perguntas simples, responda brevemente.
Explique melhor quando o senhor pedir uma explicação.

Use as memórias somente quando forem relevantes.
Nunca invente memórias.

MEMÓRIAS:
{contexto_memoria()}

CONVERSA RECENTE:
{contexto_conversa()}

PERGUNTA:
{pergunta}

Responda diretamente:
""".strip()

        inicio = time.time()

        try:
            resposta_api = (
                cliente_gemini
                .models
                .generate_content(
                    model=MODELO_GEMINI,
                    contents=prompt
                )
            )

            resposta = (
                resposta_api.text
                or ""
            ).strip()

        except Exception:
            interacao = (
                cliente_gemini
                .interactions
                .create(
                    model=MODELO_GEMINI,
                    input=prompt
                )
            )

            resposta = (
                interacao.output_text
                or ""
            ).strip()

        resposta = limpar_texto_para_voz(
            resposta
        )

        print(
            "Gemini respondeu em",
            round(
                time.time()
                - inicio,
                1
            ),
            "segundos."
        )

        status_ia = "ONLINE"

        if not resposta:
            return (
                "Senhor, não recebi uma resposta "
                "da inteligência artificial."
            )

        return resposta

    except Exception as erro:
        print(
            "ERRO GEMINI:",
            erro
        )

        status_ia = "ERRO"

        return (
            "Senhor, não consegui consultar "
            "a inteligência artificial agora."
        )


# ============================================================
# RESPOSTA CENTRAL
# ============================================================

def responder(pergunta):
    eh_memoria, resposta_memoria = comando_memoria(
        pergunta
    )

    if eh_memoria:
        return resposta_memoria

    texto = normalizar(
        pergunta
    )

    if pergunta_local(
        texto
    ):
        return responder_local(
            pergunta
        )

    return responder_gemini(
        pergunta
    )


# ============================================================
# HUD
# ============================================================

janela = tk.Tk()

janela.title(
    "J.A.R.V.I.S"
)

janela.configure(
    bg=COR_FUNDO
)

janela.geometry(
    "1100x700"
)

janela.minsize(
    800,
    550
)

canvas = tk.Canvas(
    janela,
    bg=COR_FUNDO,
    highlightthickness=0
)

canvas.pack(
    fill="both",
    expand=True
)

angulo_animacao = 0


def desenhar_hud():
    global angulo_animacao

    if not sistema_rodando:
        return

    try:
        canvas.delete(
            "all"
        )

        largura = canvas.winfo_width()
        altura = canvas.winfo_height()

        centro_x = largura // 2
        centro_y = altura // 2

        tempo_animacao = time.time()

        falando = (
            status_voz == "FALANDO"
        )

        if falando:
            pulso = (
                math.sin(
                    tempo_animacao * 9
                )
                + 1
            ) / 2

            velocidade = 8

        else:
            pulso = (
                math.sin(
                    tempo_animacao * 2
                )
                + 1
            ) / 2

            velocidade = 2


        # TÍTULO

        canvas.create_text(
            centro_x,
            45,
            text="J.A.R.V.I.S",
            fill=COR_CIANO,
            font=(
                "Consolas",
                28,
                "bold"
            )
        )

        canvas.create_text(
            centro_x,
            78,
            text="PERSONAL INTELLIGENCE SYSTEM",
            fill=COR_CIANO_ESCURO,
            font=(
                "Consolas",
                10
            )
        )


        # CÍRCULOS

        for raio in [
            165,
            135,
            105
        ]:
            canvas.create_oval(
                centro_x - raio,
                centro_y - raio,
                centro_x + raio,
                centro_y + raio,
                outline=COR_CIANO_ESCURO,
                width=1
            )


        # NÚCLEO

        if falando:
            raio_nucleo = (
                48
                + pulso * 15
            )

        else:
            raio_nucleo = (
                48
                + pulso * 3
            )

        for camada in range(
            3,
            0,
            -1
        ):
            raio_glow = (
                raio_nucleo
                + camada * 9
            )

            canvas.create_oval(
                centro_x - raio_glow,
                centro_y - raio_glow,
                centro_x + raio_glow,
                centro_y + raio_glow,
                outline=COR_CIANO_ESCURO,
                width=1
            )

        canvas.create_oval(
            centro_x - raio_nucleo,
            centro_y - raio_nucleo,
            centro_x + raio_nucleo,
            centro_y + raio_nucleo,
            outline=COR_CIANO,
            fill="#003642",
            width=(
                4
                if falando
                else 2
            )
        )


        # ONDAS QUANDO FALA

        if falando:
            for i in range(3):
                fase = (
                    tempo_animacao
                    * 80
                    + i * 28
                ) % 90

                raio_onda = (
                    70
                    + fase
                )

                canvas.create_oval(
                    centro_x - raio_onda,
                    centro_y - raio_onda,
                    centro_x + raio_onda,
                    centro_y + raio_onda,
                    outline=COR_CIANO_ESCURO,
                    width=1
                )


        # ARCOS ROTATIVOS

        canvas.create_arc(
            centro_x - 155,
            centro_y - 155,
            centro_x + 155,
            centro_y + 155,
            start=angulo_animacao,
            extent=80,
            style="arc",
            outline=COR_CIANO,
            width=3
        )

        canvas.create_arc(
            centro_x - 125,
            centro_y - 125,
            centro_x + 125,
            centro_y + 125,
            start=-angulo_animacao,
            extent=110,
            style="arc",
            outline=COR_CIANO,
            width=2
        )

        canvas.create_arc(
            centro_x - 95,
            centro_y - 95,
            centro_x + 95,
            centro_y + 95,
            start=angulo_animacao * 1.5,
            extent=65,
            style="arc",
            outline=COR_CIANO,
            width=2
        )


        # MARCAS EXTERNAS

        for angulo in range(
            0,
            360,
            15
        ):
            rad = math.radians(
                angulo
                + angulo_animacao
            )

            r1 = 175
            r2 = 185

            x1 = (
                centro_x
                + math.cos(rad)
                * r1
            )

            y1 = (
                centro_y
                + math.sin(rad)
                * r1
            )

            x2 = (
                centro_x
                + math.cos(rad)
                * r2
            )

            y2 = (
                centro_y
                + math.sin(rad)
                * r2
            )

            canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=(
                    COR_CIANO
                    if falando
                    else COR_CIANO_ESCURO
                ),
                width=1
            )


        estado = (
            "ONLINE"
            if modo_ativo
            else "STANDBY"
        )

        canvas.create_text(
            centro_x,
            centro_y - 18,
            text="J.A.R.V.I.S",
            fill=COR_TEXTO,
            font=(
                "Consolas",
                15,
                "bold"
            )
        )

        canvas.create_text(
            centro_x,
            centro_y + 10,
            text=(
                "FALANDO"
                if falando
                else estado
            ),
            fill=COR_CIANO,
            font=(
                "Consolas",
                11,
                "bold"
            )
        )


        # STATUS ESQUERDO

        canvas.create_text(
            45,
            155,
            anchor="w",
            text="SYSTEM STATUS",
            fill=COR_CIANO,
            font=(
                "Consolas",
                13,
                "bold"
            )
        )

        informacoes = [
            (
                "CAMERA",
                status_camera
            ),
            (
                "HAND TRACK",
                status_mao
            ),
            (
                "VOICE",
                status_voz
            ),
            (
                "AI",
                status_ia
            ),
            (
                "MEMORY",
                "ONLINE"
            )
        ]

        y = 195

        for nome, valor in informacoes:
            canvas.create_text(
                45,
                y,
                anchor="w",
                text=f"{nome:<12} {valor}",
                fill=COR_TEXTO,
                font=(
                    "Consolas",
                    10
                )
            )

            y += 30


        # RELÓGIO DIREITO

        agora = datetime.now()

        canvas.create_text(
            largura - 45,
            155,
            anchor="e",
            text="LOCAL SYSTEM",
            fill=COR_CIANO,
            font=(
                "Consolas",
                13,
                "bold"
            )
        )

        canvas.create_text(
            largura - 45,
            200,
            anchor="e",
            text=agora.strftime(
                "%H:%M:%S"
            ),
            fill=COR_TEXTO,
            font=(
                "Consolas",
                22,
                "bold"
            )
        )

        canvas.create_text(
            largura - 45,
            235,
            anchor="e",
            text=agora.strftime(
                "%d/%m/%Y"
            ),
            fill=COR_CIANO_ESCURO,
            font=(
                "Consolas",
                11
            )
        )


        # ÚLTIMA RESPOSTA

        texto_hud = limpar_texto_para_voz(
            ultima_fala
        )

        if len(
            texto_hud
        ) > 110:
            texto_hud = (
                texto_hud[:107]
                + "..."
            )

        canvas.create_text(
            centro_x,
            altura - 70,
            text=texto_hud,
            fill=COR_TEXTO,
            font=(
                "Consolas",
                11
            ),
            width=(
                largura - 200
            )
        )

        canvas.create_text(
            centro_x,
            altura - 30,
            text="ESC para encerrar",
            fill=COR_CIANO_ESCURO,
            font=(
                "Consolas",
                9
            )
        )


        angulo_animacao = (
            angulo_animacao
            + velocidade
        ) % 360

    except Exception as erro:
        print(
            "Erro HUD:",
            erro
        )

    if sistema_rodando:
        janela.after(
            35,
            desenhar_hud
        )


# ============================================================
# CÂMERA E CONTROLE PELA MÃO
# ============================================================

def camera_e_mao():
    global status_camera
    global status_mao
    global sistema_rodando

    mp_hands = mp.solutions.hands

    mp_draw = (
        mp.solutions.drawing_utils
    )

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.55,
        min_tracking_confidence=0.55
    )

    camera = cv2.VideoCapture(
        0
    )

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        640
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        360
    )

    camera.set(
        cv2.CAP_PROP_FPS,
        20
    )

    if not camera.isOpened():
        status_camera = "ERRO"
        status_mao = "OFFLINE"

        hands.close()

        return

    status_camera = "ONLINE"

    user32 = ctypes.windll.user32

    inicio_x = user32.GetSystemMetrics(
        76
    )

    inicio_y = user32.GetSystemMetrics(
        77
    )

    largura_total = user32.GetSystemMetrics(
        78
    )

    altura_total = user32.GetSystemMetrics(
        79
    )

    cursor_x = (
        inicio_x
        + largura_total // 2
    )

    cursor_y = (
        inicio_y
        + altura_total // 2
    )

    suavidade = 0.55
    margem = 0.12

    clicando = False

    try:
        while sistema_rodando:
            sucesso, frame = camera.read()

            if not sucesso:
                continue

            frame = cv2.flip(
                frame,
                1
            )

            altura_frame, largura_frame = (
                frame.shape[:2]
            )

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            resultado = hands.process(
                rgb
            )

            x1_area = int(
                largura_frame
                * margem
            )

            y1_area = int(
                altura_frame
                * margem
            )

            x2_area = int(
                largura_frame
                * (1 - margem)
            )

            y2_area = int(
                altura_frame
                * (1 - margem)
            )

            cv2.rectangle(
                frame,
                (
                    x1_area,
                    y1_area
                ),
                (
                    x2_area,
                    y2_area
                ),
                (
                    0,
                    255,
                    255
                ),
                1
            )

            cv2.putText(
                frame,
                "AREA DE CONTROLE",
                (
                    x1_area,
                    max(
                        20,
                        y1_area - 8
                    )
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (
                    0,
                    255,
                    255
                ),
                1
            )

            if resultado.multi_hand_landmarks:
                status_mao = "ONLINE"

                mao = (
                    resultado
                    .multi_hand_landmarks[0]
                )

                mp_draw.draw_landmarks(
                    frame,
                    mao,
                    mp_hands.HAND_CONNECTIONS
                )

                indicador = mao.landmark[8]
                polegar = mao.landmark[4]

                ix = max(
                    margem,
                    min(
                        1 - margem,
                        indicador.x
                    )
                )

                iy = max(
                    margem,
                    min(
                        1 - margem,
                        indicador.y
                    )
                )

                nx = (
                    ix - margem
                ) / (
                    1 - 2 * margem
                )

                ny = (
                    iy - margem
                ) / (
                    1 - 2 * margem
                )

                alvo_x = (
                    inicio_x
                    + int(
                        nx
                        * largura_total
                    )
                )

                alvo_y = (
                    inicio_y
                    + int(
                        ny
                        * altura_total
                    )
                )

                cursor_x += (
                    alvo_x - cursor_x
                ) * suavidade

                cursor_y += (
                    alvo_y - cursor_y
                ) * suavidade

                user32.SetCursorPos(
                    int(cursor_x),
                    int(cursor_y)
                )

                polegar_x = int(
                    polegar.x
                    * largura_frame
                )

                polegar_y = int(
                    polegar.y
                    * altura_frame
                )

                indicador_x = int(
                    indicador.x
                    * largura_frame
                )

                indicador_y = int(
                    indicador.y
                    * altura_frame
                )

                distancia = math.hypot(
                    polegar_x
                    - indicador_x,
                    polegar_y
                    - indicador_y
                )

                if (
                    distancia < 40
                    and not clicando
                ):
                    user32.mouse_event(
                        0x0002,
                        0,
                        0,
                        0,
                        0
                    )

                    user32.mouse_event(
                        0x0004,
                        0,
                        0,
                        0,
                        0
                    )

                    clicando = True

                elif distancia > 55:
                    clicando = False

            else:
                status_mao = "PROCURANDO"

            cv2.imshow(
                "J.A.R.V.I.S - Camera",
                frame
            )

            tecla = (
                cv2.waitKey(1)
                & 0xFF
            )

            if tecla == 27:
                sistema_rodando = False
                break

    except Exception as erro:
        print(
            "Erro câmera/mão:",
            erro
        )

        status_camera = "ERRO"

    finally:
        camera.release()
        hands.close()

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


# ============================================================
# SISTEMA DE VOZ
# ============================================================

def sistema_de_voz():
    global modo_ativo
    global status_voz
    global ultima_fala

    try:
        with microfone as fonte:
            status_voz = "CALIBRANDO"

            reconhecedor.adjust_for_ambient_noise(
                fonte,
                duration=1
            )

            reconhecedor.dynamic_energy_threshold = True

            status_voz = "ESPERA"

            while sistema_rodando:

                # ============================================
                # MODO DE ESPERA
                # ============================================

                if not modo_ativo:
                    try:
                        audio = reconhecedor.listen(
                            fonte,
                            timeout=3,
                            phrase_time_limit=4
                        )

                        texto = reconhecedor.recognize_google(
                            audio,
                            language="pt-BR"
                        )

                        print(
                            "Ouvido em espera:",
                            texto
                        )

                        texto_normal = normalizar(
                            texto
                        )

                        ativou = any(
                            palavra in texto_normal
                            for palavra
                            in palavras_ativacao
                        )

                        if ativou:
                            modo_ativo = True

                            falar(
                                "À disposição senhor"
                            )

                    except sr.WaitTimeoutError:
                        pass

                    except sr.UnknownValueError:
                        pass

                    except sr.RequestError as erro:
                        print(
                            "Erro reconhecimento:",
                            erro
                        )

                        time.sleep(2)

                    continue


                # ============================================
                # MODO CONVERSA
                # ============================================

                try:
                    status_voz = "OUVINDO"

                    audio = reconhecedor.listen(
                        fonte,
                        timeout=15,
                        phrase_time_limit=20
                    )

                    pergunta = reconhecedor.recognize_google(
                        audio,
                        language="pt-BR"
                    )

                    print("")
                    print(
                        "Senhor:",
                        pergunta
                    )

                    texto_normal = normalizar(
                        pergunta
                    )

                    dormir = any(
                        comando in texto_normal
                        for comando
                        in comandos_dormir
                    )

                    if dormir:
                        falar(
                            "Como desejar senhor"
                        )

                        modo_ativo = False
                        status_voz = "ESPERA"

                        continue

                    status_voz = "PROCESSANDO"

                    resposta = responder(
                        pergunta
                    )

                    if not resposta:
                        resposta = (
                            "Senhor, não consegui "
                            "formular uma resposta."
                        )

                    print(
                        "JARVIS:",
                        resposta
                    )

                    salvar_conversa(
                        pergunta,
                        resposta
                    )

                    falar(
                        resposta
                    )

                except sr.WaitTimeoutError:
                    status_voz = "CONVERSA"

                except sr.UnknownValueError:
                    status_voz = "CONVERSA"

                except sr.RequestError as erro:
                    print(
                        "Erro reconhecimento:",
                        erro
                    )

                    status_voz = "ERRO"

                    time.sleep(2)

    except Exception as erro:
        print(
            "Erro no sistema de voz:",
            erro
        )

        status_voz = "ERRO"


# ============================================================
# ENCERRAR
# ============================================================

def encerrar(event=None):
    global sistema_rodando

    sistema_rodando = False

    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

    try:
        janela.after(
            150,
            janela.destroy
        )
    except Exception:
        pass


def verificar_sistema():
    if not sistema_rodando:
        try:
            janela.destroy()
        except Exception:
            pass

        return

    janela.after(
        250,
        verificar_sistema
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

criar_banco_memoria()

janela.bind(
    "<Escape>",
    encerrar
)

janela.protocol(
    "WM_DELETE_WINDOW",
    encerrar
)

thread_camera = threading.Thread(
    target=camera_e_mao,
    daemon=True
)

thread_voz = threading.Thread(
    target=sistema_de_voz,
    daemon=True
)

thread_camera.start()
thread_voz.start()

desenhar_hud()
verificar_sistema()

try:
    janela.mainloop()

finally:
    sistema_rodando = False

    try:
        cv2.destroyAllWindows()
    except Exception:
        pass
