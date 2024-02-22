import formBody from "@fastify/formbody";
import dotenv from "dotenv";
import Fastify from "fastify";
import pkg from "pg";
const { Pool } = pkg;

dotenv.config({ path: ".env" });

const pool = new Pool({
  user: process.env.DB_USER,
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD,
  port: process.env.DB_PORT,
});

const app = Fastify({
  logger: false,
});

app.register(formBody);

app.post("/clientes/:client_id/transacoes", async (request, reply) => {
  const client = await pool.connect();

  try {
    const client_id = request.params.client_id;
    const { valor, tipo, descricao } = request.body;
    if (!Number.isInteger(valor) || valor < 0) {
      return reply
        .type("application/json")
        .code(422)
        .send({ error: "Valor inválido" });
    }

    if (tipo !== "d" && tipo !== "c") {
      return reply
        .type("application/json")
        .code(422)
        .send({ error: "Tipo inválido" });
    }

    if (
      !descricao ||
      typeof descricao !== "string" ||
      descricao.trim().length < 1 ||
      descricao.trim().length > 10
    ) {
      return reply
        .type("application/json")
        .code(422)
        .send({ error: "Descrição inválida" });
    }

    // await client.query("BEGIN");
    const userQuery = `SELECT saldo, limite FROM clientes WHERE id = $1`;
    const userResult = await client.query(userQuery, [client_id]);

    if (userResult.rows.length === 0) {
      // await client.query("ROLLBACK");
      return reply
        .type("application/json")
        .code(404)
        .send({ error: "Cliente não encontrado" });
    }

    let { saldo, limite } = userResult.rows[0];

    if (tipo === "d") {
      const debitValue = valor * -1;
      if (saldo + debitValue < limite) {
        // await client.query("ROLLBACK");
        return reply
          .type("application/json")
          .code(422)
          .send({ error: "Saldo insuficiente" });
      } else {
        saldo += debitValue;
      }
    }

    if (tipo === "c") {
      saldo += valor;
    }

    await client.query("BEGIN");
    const updateQuery = `UPDATE clientes SET saldo = $1 WHERE id = $2`;
    await client.query(updateQuery, [saldo, client_id]);

    const date_to_string = new Date().toISOString();
    const insertQuery = `INSERT INTO transacoes (valor, tipo, descricao, realizado_em, cliente_id) VALUES ($1, $2, $3, $4, $5)`;
    await client.query(insertQuery, [
      valor,
      tipo,
      descricao,
      date_to_string,
      client_id,
    ]);

    await client.query("COMMIT");
    return reply.type("application/json").code(200).send({ limite, saldo });
  } catch (error) {
    // console.log(error);
    await client.query("ROLLBACK");
    // process.exit(1);
    return reply
      .type("application/json")
      .code(500)
      .send({ error: "Internal Server Error" });
  } finally {
    client.release();
  }
});

app.get("/clientes/:client_id/extrato", async (request, reply) => {
  const client_id = request.params.client_id;
  // const client = await pool.connect();
  try {
    const clientQuery = `SELECT saldo, limite FROM clientes WHERE id = $1;`;
    const clientResult = await pool.query(clientQuery, [client_id]);

    if (clientResult.rows.length === 0) {
      // await client.query("ROLLBACK");
      return reply.code(404).send({ detail: "Cliente não encontrado" });
    }

    const { saldo, limite } = clientResult.rows[0];

    const transacoesQuery = `SELECT valor, tipo, descricao, realizado_em FROM transacoes WHERE cliente_id = $1 ORDER BY realizado_em DESC LIMIT 10;`;
    const transacoesResult = await pool.query(transacoesQuery, [client_id]);

    const ultimasTransacoes = transacoesResult.rows.map((t) => ({
      valor: t.valor,
      tipo: t.tipo,
      descricao: t.descricao,
      realizada_em: t.realizado_em,
    }));

    const resultado = {
      saldo: {
        total: saldo,
        data_extrato: new Date().toISOString(),
        limite: limite,
      },
      ultimas_transacoes: ultimasTransacoes,
    };

    return reply.send(resultado);
  } catch (error) {
    // await client.query("ROLLBACK");
    return reply.code(500).send({ detail: "Internal Server Error" });
  } finally {
    client.release();
  }
});

const port = process.env.APP_PORT || 3000;
const appHost = process.env.APP_HOST || "localhost";

app.listen({ port: port, host: appHost }, (err) => {
  if (err) {
    console.log(err);
    process.exit(1);
  }
  console.log(`Server running on port ${port}`);
});
