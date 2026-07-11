from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
OUTPUT = DATA_DIR / 'transacoes_fake.csv'

STATUSES = ['pago', 'pendente', 'falha']
STATUS_VARIANTS = ['PAGO', 'Pago', 'pendente', 'PENDENTE', 'falha', 'FALHA', 'Falha']
DATE_FORMATS = ['%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y', '%Y/%m/%d']


def _make_row(i: int, base_date: datetime) -> dict[str, str]:
    dt = base_date + timedelta(days=i % 60)
    amount = round(random.uniform(20, 2000), 2)
    customer_id = f'C{1000 + i:05d}'
    status = random.choice(STATUS_VARIANTS)
    date_text = dt.strftime(random.choice(DATE_FORMATS))

    if i % 17 == 0:
        customer_id = ''
    if i % 11 == 0:
        amount = -amount
    if i % 20 == 0:
        status = status.upper()

    return {
        'customer_id': customer_id,
        'transaction_date': date_text,
        'amount': f'{amount:.2f}',
        'status': status,
    }


def main() -> None:
    random.seed(42)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    base_date = datetime(2026, 7, 1)
    rows = []

    for i in range(1, 501):
        row = _make_row(i, base_date)
        rows.append(row)
        if i % 16 == 0:
            rows.append(dict(row))

    with OUTPUT.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['customer_id', 'transaction_date', 'amount', 'status'])
        writer.writeheader()
        writer.writerows(rows)

    print(f'Gerado: {OUTPUT} ({len(rows)} linhas)')


if __name__ == '__main__':
    main()
