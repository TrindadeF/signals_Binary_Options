from telethon import events
import re
from datetime import datetime
import asyncio

class TelegramHandler:
    def __init__(self, client, iq_handler):
        self.client = client
        self.iq_handler = iq_handler

    async def handle_message(self, event):
        message = event.message.message
        print(f"Mensagem recebida: {message}")

        ativo_pattern = re.compile(r"ATIVO:\s*([\w-]+)")
        horario_pattern = re.compile(r"HORÁRIO:\s*(\d{2}:\d{2}:\d{2})")
        direcao_pattern = re.compile(r"DIREÇÃO:\s*(\w+)")
        expiracao_pattern = re.compile(r"EXPIRAÇÃO:\s*(\d+)M")

        ativo_match = ativo_pattern.search(message)
        horario_match = horario_pattern.search(message)
        direcao_match = direcao_pattern.search(message)
        expiracao_match = expiracao_pattern.search(message)

        if ativo_match and horario_match and direcao_match and expiracao_match:
            ativo = ativo_match.group(1)
            horario = horario_match.group(1)
            direcao = direcao_match.group(1)
            expiracao = int(expiracao_match.group(1))

            print(f"Detalhes da Mensagem Extraídos:")
            print(f"  Ativo: {ativo}")
            print(f"  Horário: {horario}")
            print(f"  Direção: {direcao}")
            print(f"  Expiração: {expiracao}M")

            horario_atual = datetime.now()
            horario_ordem = datetime.strptime(horario, "%H:%M:%S").replace(
                year=horario_atual.year,
                month=horario_atual.month,
                day=horario_atual.day
            )

            if horario_ordem < horario_atual:
                print("Horário da mensagem já passou. Ordem não enviada.")
                return

            tempo_espera = (horario_ordem - horario_atual).total_seconds()
            print(f"Aguardando {tempo_espera:.2f} segundos até o horário da ordem...")
            await asyncio.sleep(tempo_espera)

            print("Enviando ordem para a corretora...")
            await self.iq_handler.execute_order(ativo, direcao, expiracao)
        else:
            print("Não foi possível extrair todas as informações da mensagem.")

    async def start(self):
        print("Iniciando cliente Telethon...")
        await self.client.start()
        self.client.add_event_handler(self.handle_message, events.NewMessage(chats=-4675899854))
        print("Cliente Telethon conectado e eventos registrados.")
        await self.client.run_until_disconnected()