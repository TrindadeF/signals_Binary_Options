from asyncio.log import logger
from telethon import events
import re
from datetime import datetime, timedelta
import asyncio

class TelegramHandler:
    def __init__(self, client, iq_handler):
        self.client = client
        self.iq_handler = iq_handler

    async def handle_message(self, event):
        message = event.message.message
        logger.info(f"📩 Mensagem recebida: {message}")

        ativo_match = re.search(r"ATIVO:\s*([\w-]+)", message)
        horario_match = re.search(r"HORÁRIO:\s*(\d{2}:\d{2}:\d{2})", message)
        direcao_match = re.search(r"DIREÇÃO:\s*(\w+)", message)
        expiracao_match = re.search(r"EXPIRAÇÃO:\s*(\d+)M", message)

        if not (ativo_match and horario_match and direcao_match and expiracao_match):
            logger.error("❌ Erro: Não foi possível extrair todas as informações da mensagem.")
            return

        ativo = ativo_match.group(1)
        horario = horario_match.group(1)
        direcao = direcao_match.group(1)
        expiracao = int(expiracao_match.group(1))

        logger.info(f"📌 Detalhes extraídos: Ativo={ativo}, Horário={horario}, Direção={direcao}, Expiração={expiracao}M")

        horario_atual = datetime.now()
        horario_ordem = datetime.strptime(horario, "%H:%M:%S").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )

        if horario_ordem < horario_atual:
            logger.warning("⚠️ Horário da mensagem já passou. Ordem não será enviada.")
            return

        tempo_espera = (horario_ordem - horario_atual).total_seconds()

        logger.info(f"⏳ Aguardando {tempo_espera:.2f} segundos até o horário da ordem...")
        await self.iq_handler.process_trade_signal(ativo, direcao, expiracao, horario_ordem)


    async def start(self):
        print("Iniciando cliente Telethon...")
        await self.client.start()
        self.client.add_event_handler(self.handle_message, events.NewMessage(chats=-4675899854))
        print("Cliente Telethon conectado e eventos registrados.")
        await self.client.run_until_disconnected()