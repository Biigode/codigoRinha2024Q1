from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone
from enum import Enum
from database import DataBaseConnector  # Certifique-se de que esta é a versão síncrona


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


db = DataBaseConnector()
app = FastAPI()


@app.post(
    "/clientes/{client_id}/transacoes",
    status_code=200,
    response_model=TransacaoResposta,
)
async def transacoes(client_id: int, transacao: TransacaoEntrada):
    if len(transacao.descricao) > 10:
        raise HTTPException(
            status_code=422, detail="Descrição não pode ter mais que 10 caracteres"
        )

    query = f"SELECT * FROM clientes WHERE id = {client_id};"
    user_founded = await db.execute_query(query)
    if user_founded is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    cents = transacao.valor
    user_id, user_limite, user_saldo = user_founded[0], user_founded[1], user_founded[2]

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
    # db.close_connection()
    return TransacaoResposta(limite=user_limite, saldo=user_saldo)


@app.get("/clientes/{client_id}/extrato", status_code=200)
async def extrato(client_id: int):
    query = f"SELECT saldo, limite FROM clientes WHERE id = {client_id};"
    user_founded = await db.execute_query(query)
    if user_founded is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Novamente, ajuste os índices conforme necessário
    saldo, limite = user_founded[0], user_founded[1]

    query = f"SELECT valor, tipo, descricao, realizado_em FROM transacoes WHERE cliente_id = {client_id} ORDER BY realizado_em DESC LIMIT 10;"
    ultimas_transacoes = await db.execute_query(query, multi=True)

    resultado = ExtratoResposta(
        saldo=Saldo(
            total=saldo, data_extrato=datetime.now(timezone.utc), limite=limite
        ),
        ultimas_transacoes=[
            TransacaoExtrato(valor=t[0], tipo=t[1], descricao=t[2], realizada_em=t[3])
            for t in ultimas_transacoes
        ],
    )
    # db.close_connection()
    return resultado
