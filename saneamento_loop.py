from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
INPUT = DATA_DIR / 'transacoes_fake.csv'
OUTPUT = DATA_DIR / 'transacoes_limpo.csv'
REPORT = DATA_DIR / 'quality_report.json'
MAX_CYCLES = 4
ALLOWED_STATUS = {'pago', 'pendente', 'falha'}
DATE_INPUTS = ['%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y', '%Y/%m/%d']
CRITERIA = ['customer_id', 'amount', 'transaction_date', 'status', 'duplicates']


def _read_rows(path: Path):
    with path.open('r', encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh))


def _write_rows(path: Path, rows):
    with path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['customer_id', 'transaction_date', 'amount', 'status'])
        writer.writeheader()
        writer.writerows(rows)


def _parse_date(value: str):
    for fmt in DATE_INPUTS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _normalize_status(value: str):
    normalized = value.strip().lower()
    if normalized in ALLOWED_STATUS:
        return normalized
    aliases = {
        'paid': 'pago',
        'pago': 'pago',
        'pending': 'pendente',
        'pendente': 'pendente',
        'failed': 'falha',
        'falha': 'falha',
    }
    return aliases.get(normalized)


def _evaluate(rows):
    seen = set()
    counts = Counter({key: 0 for key in CRITERIA})
    for row in rows:
        if not row.get('customer_id', '').strip():
            counts['customer_id'] += 1

        amount = row.get('amount', '').strip()
        try:
            if float(amount) < 0:
                counts['amount'] += 1
        except ValueError:
            counts['amount'] += 1

        date_raw = row.get('transaction_date', '').strip()
        date_iso = _parse_date(date_raw)
        if date_iso is None or date_iso != date_raw:
            counts['transaction_date'] += 1

        status_raw = row.get('status', '').strip()
        normalized = _normalize_status(status_raw)
        if normalized not in ALLOWED_STATUS or normalized != status_raw:
            counts['status'] += 1

        key = tuple(row.get(col, '') for col in ('customer_id', 'transaction_date', 'amount', 'status'))
        if key in seen:
            counts['duplicates'] += 1
        else:
            seen.add(key)
    return counts


def _saneamento_cycle(rows):
    discarded = 0
    corrected = Counter()
    cleaned = []
    seen = set()

    for row in rows:
        customer_id = row.get('customer_id', '').strip()
        if not customer_id:
            discarded += 1
            continue

        amount_raw = row.get('amount', '').strip()
        try:
            amount = float(amount_raw)
        except ValueError:
            amount = 0.0
        if amount < 0:
            amount = abs(amount)
            corrected['amount'] += 1

        date_raw = row.get('transaction_date', '').strip()
        date_iso = _parse_date(date_raw)
        if date_iso is None:
            date_iso = datetime.utcnow().date().isoformat()
            corrected['transaction_date'] += 1
        elif date_iso != date_raw:
            corrected['transaction_date'] += 1

        status_raw = row.get('status', '').strip()
        status = _normalize_status(status_raw)
        if status is None:
            status = 'pendente'
            corrected['status'] += 1
        elif status != status_raw:
            corrected['status'] += 1

        cleaned_row = {
            'customer_id': customer_id,
            'transaction_date': date_iso,
            'amount': f'{amount:.2f}',
            'status': status,
        }
        key = tuple(cleaned_row.values())
        if key in seen:
            corrected['duplicates'] += 1
            continue
        seen.add(key)
        cleaned.append(cleaned_row)

    return cleaned, corrected, discarded


def main() -> None:
    if not INPUT.exists():
        raise SystemExit(f'Arquivo nao encontrado: {INPUT}. Rode gerar_fake.py primeiro.')

    rows = _read_rows(INPUT)
    report = {
        'input_file': str(INPUT),
        'output_file': str(OUTPUT),
        'cycles': [],
        'discarded_rows': 0,
        'corrected_rows': {key: 0 for key in CRITERIA},
        'initial_problems': dict(_evaluate(rows)),
        'final_status': {key: 'reprovado' for key in CRITERIA},
        'final_problems': {key: 0 for key in CRITERIA},
        'approved': False,
    }

    for cycle in range(1, MAX_CYCLES + 1):
        problems = _evaluate(rows)
        report['cycles'].append({'cycle': cycle, 'problems': dict(problems)})
        print(f'ciclo {cycle}: ' + ', '.join(f'{k}={v}' for k, v in problems.items()))
        if not any(problems.values()):
            break
        rows, corrected, discarded = _saneamento_cycle(rows)
        report['discarded_rows'] += discarded
        for key, value in corrected.items():
            report['corrected_rows'][key] = report['corrected_rows'].get(key, 0) + value

    final_problems = _evaluate(rows)
    report['final_status'] = {k: ('aprovado' if final_problems.get(k, 0) == 0 else 'reprovado') for k in CRITERIA}
    report['final_problems'] = {k: final_problems.get(k, 0) for k in CRITERIA}
    report['approved'] = all(v == 0 for v in report['final_problems'].values())

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _write_rows(OUTPUT, rows)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'relatorio: {REPORT}')
    print(f'saida: {OUTPUT}')


if __name__ == '__main__':
    main()
