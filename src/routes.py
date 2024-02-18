from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Supondo que 'database' é o módulo onde sua classe DataBaseConnector assíncrona está definida
from database import DataBaseConnector


class Tipo(str, Enum):
    credito = "c"
    debito = "d"


class TransacaoEntrada(BaseModel):
    valor: int = Field(gt=0, description="Valor em centavos")
    tipo: Tipo
    descricao: str = Field(..., min_length=1, max_length=10)


class TransacaoExtrato(BaseModel):
    valor: int
    tipo: Tipo
    descricao: str
    realizada_em: datetime


class Saldo(BaseModel):
    total: int
    data_extrato: datetime
    limite: int


class ExtratoResposta(BaseModel):
    saldo: Saldo
    ultimas_transacoes: List[TransacaoExtrato]


class TransacaoResposta(BaseModel):
    limite: int
    saldo: int


# Cria uma instância global do conector do banco de dados
db = DataBaseConnector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_pool()
    yield
    await db.close_pool()


app = FastAPI(lifespan=lifespan)


@app.post(
    "/clientes/{client_id}/transacoes",
    status_code=200,
    response_model=TransacaoResposta,
)
async def transacoes(client_id: int, transacao: TransacaoEntrada):
    """
    Realiza uma transação para um cliente específico.

    Args:
        client_id (int): O ID do cliente.
        transacao (TransacaoEntrada): Os dados da transação a ser realizada.

    Raises:
        HTTPException: Se a descrição da transação tiver mais de 10 caracteres.
        HTTPException: Se o cliente não for encontrado.
        HTTPException: Se o saldo for insuficiente para uma transação de débito.

    Returns:
        TransacaoResposta: Os dados da transação realizada, incluindo o limite e saldo atualizados.
    """

    if len(transacao.descricao) > 10:
        raise HTTPException(
            status_code=422, detail="Descrição não pode ter mais que 10 caracteres"
        )

    query = f"SELECT * FROM clientes WHERE id = {client_id};"
    user_founded = await db.execute_query(query)

    if user_founded is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    cents = transacao.valor
    user_id = user_founded["id"]
    user_limite = user_founded["limite"]
    user_saldo = user_founded["saldo"]

    if transacao.tipo == Tipo.debito:
        if user_saldo - cents < -user_limite:
            raise HTTPException(status_code=422, detail="Saldo insuficiente")
        user_saldo -= cents
    else: 
        user_saldo += cents

    update_query = f"UPDATE clientes SET saldo = {user_saldo} WHERE id = {user_id};"
    await db.execute_insert_query(update_query)

    date_to_string = datetime.now(timezone.utc).isoformat()
    insert_query = f"INSERT INTO transacoes (valor, tipo, descricao, realizado_em, cliente_id) VALUES ({cents}, '{transacao.tipo.value}', '{transacao.descricao}', '{date_to_string}', {client_id});"
    await db.execute_insert_query(insert_query)

    return TransacaoResposta(limite=user_limite, saldo=user_saldo)


@app.get("/clientes/{client_id}/extrato", status_code=200)
async def extrato(client_id: int):
    """
    Retorna o extrato bancário de um cliente.

    Args:
        client_id (int): O ID do cliente.

    Returns:
        dict: Um dicionário contendo informações sobre o saldo total, data do extrato, limite e as últimas transações do cliente.
    """

    query = f"SELECT saldo, limite FROM clientes WHERE id = {client_id};"
    user_founded = await db.execute_query(query)

    if user_founded is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    query = f"SELECT valor, tipo, descricao, realizado_em FROM transacoes WHERE cliente_id = {client_id} ORDER BY realizado_em DESC LIMIT 10;"

    ultimas_transacoes = await db.execute_query(query, multi=True)

    resultado = {
        "saldo": {
            "total": user_founded["saldo"],
            "data_extrato": datetime.now(timezone.utc).isoformat(),
            "limite": user_founded["limite"],
        },
        "ultimas_transacoes": [
            {
                "valor": transacao["valor"],
                "tipo": transacao["tipo"],
                "descricao": transacao["descricao"],
                "realizada_em": transacao["realizado_em"].isoformat(),
            }
            for transacao in ultimas_transacoes
        ],
    }
    return resultado
