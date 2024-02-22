import compression from "compression";
import dotenv from "dotenv";
import express from "express";
import { check, validationResult } from "express-validator";
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

const app = express();
app.use(express.json());
app.use(compression());

app.post(
  "/clientes/:client_id/transacoes",
  [
    check("client_id").isNumeric(),
    check("valor").isInt({ min: 0, gt: 0 }),
    check("tipo").isIn(["c", "d"]),
    check("descricao").isString().isLength({ min: 1, max: 10 }),
  ],
  async (req, res, next) => {
    let client;
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(422).json({ errors: errors.array() });
      }

      const client_id = req.params.client_id;
      const { valor, tipo, descricao } = req.body;

      client = await pool.connect();

      const userQuery = `SELECT saldo, limite FROM clientes WHERE id = $1`;
      const userResult = await client.query(userQuery, [client_id]);

      console.log(userResult.rows.length);

      if (userResult.rows.length === 0) {
        return res.status(404).json({ error: "Cliente não encontrado" });
      }

      let { saldo, limite } = userResult.rows[0];
      const cents = valor;

      if (tipo === "d" && saldo - cents < -limite) {
        return res.status(422).json({ error: "Saldo insuficiente" });
      }

      saldo += tipo === "d" ? -cents : cents;

      await client.query("BEGIN");
      const updateQuery = `UPDATE clientes SET saldo = $1 WHERE id = $2`;
      await client.query(updateQuery, [saldo, client_id]);

      const date_to_string = new Date().toISOString();
      const insertQuery = `INSERT INTO transacoes (valor, tipo, descricao, realizado_em, cliente_id) VALUES ($1, $2, $3, $4, $5)`;
      await client.query(insertQuery, [
        cents,
        tipo,
        descricao,
        date_to_string,
        client_id,
      ]);

      await client.query("COMMIT");
      res.json({ limite, saldo });
    } catch (error) {
      console.log(error);
      if (client) {
        await client.query("ROLLBACK");
      }
    } finally {
      if (client) client.release();
    }
  }
);

app.get(
  "/clientes/:client_id/extrato",
  [check("client_id").isNumeric()],
  async (req, res) => {
    const client_id = req.params.client_id;

    try {
      const clientQuery = `SELECT saldo, limite FROM clientes WHERE id = $1;`;
      const clientResult = await pool.query(clientQuery, [client_id]);

      if (clientResult.rows.length === 0) {
        return res.status(404).json({ detail: "Cliente não encontrado" });
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

      res.json(resultado);
    } catch (error) {
      console.log(error);
      res.status(500).json({ detail: "Internal Server Error" });
    }
  }
);

const port = process.env.APP_PORT || 3000;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
// }
