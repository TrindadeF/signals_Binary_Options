from iqoptionapi.stable_api import IQ_Option
import asyncio
import time

class IQHandler:
    def __init__(self):
        self.iq = IQ_Option("SEU_EMAIL", "SUA_SENHA")
        self.connect()

    def connect(self, retries=5, delay=2):
        for attempt in range(retries):
            try:
                if self.iq.connect():
                    print("Conectado à IQOption com sucesso!")
                    return True
                else:
                    print(f"Falha ao conectar à IQOption. Tentativa {attempt + 1} de {retries}.")
                    time.sleep(delay)
            except Exception as e:
                print(f"Erro ao conectar: {e}. Tentativa {attempt + 1} de {retries}.")
                time.sleep(delay)
        print("Falha ao conectar após múltiplas tentativas.")
        return False

    def ensure_connection(self, retries=3, delay=2):
        if not self.iq.check_connect():
            print("Conexão perdida. Tentando reconectar...")
            self.connect(retries=retries, delay=delay)

    async def execute_order(self, ativo, direcao, expiracao, valor=10, retries=3, delay=5):
        self.ensure_connection()

        valor = float(valor)

        try:
            saldo_real = self.iq.get_balance()
            if saldo_real < valor:
                print(f"Saldo insuficiente na conta real (Saldo: {saldo_real}). Redirecionando para conta demo.")
                if not self.iq.change_balance("PRACTICE"):
                    print("Erro ao alterar para a conta demo. Ordem não executada.")
                    return
        except Exception as e:
            print(f"Erro ao verificar saldo ou mudar conta: {e}")
            return

        for attempt in range(retries):
            self.ensure_connection()
            try:
                if direcao.lower() == "call":
                    resultado = self.iq.buy(valor, ativo, "call", expiracao)
                elif direcao.lower() == "put":
                    resultado = self.iq.buy(valor, ativo, "put", expiracao)
                else:
                    print("Direção inválida.")
                    return

                if resultado:
                    print(f"Ordem executada com sucesso! Ativo: {ativo}, Direção: {direcao}, Expiração: {expiracao}M")
                    return
                else:
                    print("Falha ao executar a ordem. Tentando novamente...")
                    await asyncio.sleep(delay)
            except Exception as e:
                print(f"Erro ao executar a ordem: {e}. Tentativa {attempt + 1} de {retries}.")
                await asyncio.sleep(delay)
        print("Falha ao executar a ordem após múltiplas tentativas.")