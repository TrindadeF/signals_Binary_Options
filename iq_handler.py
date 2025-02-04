import asyncio
import logging
import time
import asyncio
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta
import getpass

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class IQHandler:
    def __init__(self, email=None, password=None):
        self.iq = None
        self.connected = False
        self.email = email if email else input("📧 Digite seu email da IQ Option: ")
        self.password = password if password else getpass.getpass("🔑 Digite sua senha da IQ Option: ")

    async def connect(self, retries=5, delay=5):
        for attempt in range(1, retries + 1):
            try:
                self.iq = IQ_Option(self.email, self.password)
                success = await asyncio.get_event_loop().run_in_executor(None, self.iq.connect)

                if success and self.iq.check_connect():
                    self.connected = True
                    logger.info("✅ Conectado à IQOption com sucesso!")

                    if not await self.set_practice_account():
                        logger.error("❌ Falha ao alternar para conta prática")
                        return False

                    return True

                logger.warning(f"⚠️ Conexão falhou (tentativa {attempt}/{retries})")
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"❌ Erro na conexão: {str(e)}")
                await asyncio.sleep(delay)

        self.connected = False
        logger.error("❌ Falha permanente na conexão")
        return False

    async def safe_retry(self, func, *args, **kwargs):
        delay = 1  
        for attempt in range(5): 
            try:
                result = await asyncio.get_event_loop().run_in_executor(None, lambda: func(*args, **kwargs))
                if result is None:
                    logger.warning(f"⚠️ {func.__name__} retornou None na tentativa {attempt + 1}")
                return result
            except Exception as e:
                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {str(e)}")
                await self.reconnect() 
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8)  
        logger.error(f"❌ Todas as tentativas falharam para o método {func.__name__}")
        return None



    async def reconnect(self):
        logger.warning("⚠️ Tentando reconectar à IQ Option...")
        
        try:
            self.iq.api.close()  
        except AttributeError:
            pass  

        self.connected = False

        return await self.connect()

    async def set_practice_account(self):
        try:
            if not await self.check_connection():
                logger.error("❌ Conexão perdida antes de alternar para conta prática.")
                return False

            account_type = await self.safe_retry(self.iq.get_balance_mode)
            logger.info(f"📢 Modo de conta atual: {account_type}")

            if account_type == "PRACTICE":
                logger.info("✅ Já estamos na conta prática.")
                return True  

            logger.info("🔄 Alternando para conta prática...")

            result = await self.safe_retry(self.iq.change_balance, "PRACTICE")

            if not result:
                logger.error("❌ Falha ao alternar para conta prática.")
                return False

            account_type = await self.safe_retry(self.iq.get_balance_mode)
            if account_type != "PRACTICE":
                logger.error(f"❌ Tipo de conta incorreto após tentativa: {account_type}")
                return False

            logger.info("✅ Conta prática selecionada com sucesso")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao selecionar conta prática: {str(e)}")
            return False

    async def check_connection(self):
        if not self.connected or not await self.safe_retry(self.iq.check_connect):
            logger.warning("⚠️ Conexão perdida, reconectando...")
            return await self.reconnect()
        return True

    async def get_balance(self):
        if await self.check_connection():
            return await self.safe_retry(self.iq.get_balance)
        return None


    async def process_trade_signal(self, ativo, direcao, expiracao, horario_alvo):
        agora = datetime.now()

        ativo_normalizado = await self.normalize_asset_name(ativo)
        if not ativo_normalizado:
            logger.error(f"❌ Não foi possível normalizar o ativo {ativo}. Ordem cancelada.")
            return

        if not await self.is_asset_open(ativo_normalizado):
            logger.error(f"❌ O ativo {ativo_normalizado} está suspenso ou não disponível.")
            return

        antecedencia = 25 if expiracao == 1 else 20
        horario_envio = horario_alvo - timedelta(seconds=antecedencia)
        tempo_restante = (horario_envio - agora).total_seconds()

        if tempo_restante <= 0:
            logger.error("❌ Não é possível aguardar. O horário de envio já passou.")
            return

        logger.info(f"⏳ Aguardando {tempo_restante:.2f} segundos para enviar a ordem...")
        await asyncio.sleep(tempo_restante)

        if not await self.is_asset_open(ativo_normalizado):
            logger.error(f"❌ O ativo {ativo_normalizado} está suspenso no momento da execução. Ordem cancelada.")
            return

        await self.execute_order(ativo_normalizado, direcao, expiracao, horario_alvo)



    async def get_available_assets(self):
        try:
            open_assets = await self.safe_retry(self.iq.get_all_open_time)
            if not open_assets:
                logger.error("❌ Nenhum ativo disponível na API da IQ Option.")
                return {}

            asset_map = {}
            for market in ["digital", "binary"]:
                if market in open_assets:
                    for asset_code, asset_info in open_assets[market].items():
                        if asset_info["open"]:
                            asset_map[asset_code.replace("-", "/")] = asset_code

            logger.info(f"📜 Ativos disponíveis: {asset_map}")
            return asset_map

        except Exception as e:
            logger.error(f"❌ Erro ao obter ativos disponíveis: {str(e)}")
            return {}

    async def normalize_asset_name(self, asset_name):
        normalized_name = asset_name.strip().replace(" ", "").replace("\n", "").replace("-OTC", "/OTC").replace("-", "")

        asset_map = await self.get_available_assets()
        logger.info(f"📜 Mapeamento de ativos disponíveis: {asset_map}")

        possible_variants = [
            f"{normalized_name}/op",  
            f"{normalized_name}-op",  
            f"{normalized_name}/OTC",  
            f"{normalized_name}-OTC",  
            normalized_name  
        ]

        for variant in possible_variants:
            if variant in asset_map:
                logger.info(f"✅ Ativo normalizado encontrado: {variant} -> {asset_map[variant]}")
                return asset_map[variant]

        logger.error(f"❌ Ativo {asset_name} não encontrado nos ativos disponíveis.")
        return None




    async def execute_order(self, ativo, direcao, expiracao, horario_alvo, valor=10):
        tipo_mercado = "digital" if "/op" in ativo else "binary"  
        ativo_limpo = ativo.replace("/op", "").replace("/OTC", "")  

        try:
            if not await self.check_connection():
                logger.error("❌ Não conectado para executar ordem")
                return False

            agora = datetime.now()
            if (agora - horario_alvo).total_seconds() > 30:
                logger.error("❌ Ordem cancelada! O horário de execução já expirou.")
                return False

            if tipo_mercado == "digital":
                logger.info(f"📊 Tentando abrir ordem digital com ativo: {ativo_limpo}")
                
                position_id = await self.safe_retry(self.iq.buy_digital_spot, ativo_limpo, valor, direcao.lower())
                
                if position_id is None or position_id == -1:
                    logger.error("❌ Falha ao abrir ordem digital.")
                    return False
                logger.info("✅ Ordem digital aberta com sucesso!")

            else:
                logger.info(f"📊 Executando ordem binária com ativo: {ativo_limpo}")

                result = await self.safe_retry(self.iq.buy, valor, ativo_limpo, direcao.lower(), expiracao)

                if not result or not isinstance(result, tuple) or not result[0]:
                    logger.error(f"❌ Ordem binária falhou! Retorno da API: {result}")
                    return False

            logger.info(f"✅ Ordem enviada com sucesso!")
            return True

        except Exception as e:
            logger.error(f"❌ Erro crítico na execução da ordem: {str(e)}")
            return False




    async def is_asset_open(self, ativo):
        open_assets = await self.safe_retry(self.iq.get_all_open_time)

        for market in ["binary", "digital"]:
            if ativo in open_assets.get(market, {}):
                status = open_assets[market][ativo]["open"]
                if status:
                    logger.info(f"✅ O ativo {ativo} está aberto para negociação.")
                    return True
                else:
                    logger.warning(f"⚠️ O ativo {ativo} está suspenso no momento.")
                    return False

        logger.error(f"❌ O ativo {ativo} não foi encontrado nos mercados disponíveis.")
        return False

