# Loop de Saneamento de Dados Transacionais

Protótipo de um **loop de qualidade de dados**: valida e auto-corrige um dataset
transacional até passar em todos os critérios — com **condição de parada** e
**relatório de auditoria**. Um padrão de engenharia de dados aplicável a
conciliação e confiabilidade de cobrança recorrente.

> 100% offline · só biblioteca padrão do Python · dados 100% sintéticos.

## O padrão

Em vez de um script de limpeza *one-shot*, o saneamento roda em **ciclos**:

1. **Mede** quantos problemas restam por critério.
2. **Corrige** o que dá pra corrigir.
3. **Re-mede.**
4. **Para** quando zera *ou* atinge o teto de iterações — nunca roda indefinidamente.

Cada execução emite um `quality_report.json` auditável: problemas antes,
corrigidos, linhas descartadas e status final por critério.

## Critérios de qualidade

| # | Critério | Correção |
|---|---|---|
| 1 | `customer_id` sem nulos | linha descartada e registrada |
| 2 | `amount` sem negativos | convertido para positivo |
| 3 | `transaction_date` em ISO 8601 | normalizado |
| 4 | `status` ∈ {pago, pendente, falha} | normalizado |
| 5 | sem duplicatas | mantém o 1º registro |

## Uso

```powershell
python gerar_fake.py       # gera o dataset sintético "sujo"
python saneamento_loop.py  # roda o loop e emite o relatório
```

Saída em `data/` (git-ignored): `transacoes_fake.csv`, `transacoes_limpo.csv`,
`quality_report.json`.

## Resultado de referência

Com ~530 linhas sintéticas e 5 tipos de defeito injetados, converge em
**2 ciclos** com todos os critérios aprovados.

---

Protótipo por **AAPSON**. Sem dados reais, sem dependências externas.
