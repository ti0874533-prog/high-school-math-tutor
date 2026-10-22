"""Read-only exam manifest checks; source authenticity requires human/tool review."""
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse


def check(data):
    errors = []

    def number(value, label, positive=True):
        try:
            if isinstance(value, bool):
                raise ValueError()
            result = Decimal(str(value))
            if not result.is_finite() or (result <= 0 if positive else result < 0):
                raise ValueError()
            return result
        except (InvalidOperation, ValueError):
            errors.append(label + ': invalid score')
            return Decimal(0)

    if not isinstance(data, dict):
        return ['manifest must be an object']
    target = number(data.get('target_total'), 'target_total')
    order = data.get('type_order')
    if not isinstance(order, list) or not order or any(not isinstance(x, str) or not x.strip() for x in order):
        return errors + ['type_order must be a nonempty string list']
    if len(set(order)) != len(order):
        errors.append('duplicate question types in type_order')
    questions = data.get('questions')
    if not isinstance(questions, list) or not questions:
        return errors + ['questions must be a nonempty list']
    ranges = data.get('year_ranges', {})
    if not isinstance(ranges, dict):
        return errors + ['year_ranges must be an object']
    for kind, bounds in ranges.items():
        if not isinstance(bounds, list) or len(bounds) != 2 or any(type(y) is not int for y in bounds) or bounds[0] > bounds[1]:
            return errors + [f'invalid year range: {kind}']
    for flag in ['require_real_sources', 'preserve_source_points']:
        if flag in data and type(data[flag]) is not bool:
            errors.append(flag + ' must be boolean')
    total, previous, seen = Decimal(0), -1, set()
    for index, q in enumerate(questions, 1):
        if not isinstance(q, dict):
            errors.append(f'question {index}: must be object')
            continue
        label = f'question {index}'
        qid = q.get('id')
        if not isinstance(qid, str) or not qid.strip() or qid in seen:
            errors.append(label + ': missing/duplicate string id')
        else:
            seen.add(qid)
        kind = q.get('type')
        if kind not in order:
            errors.append(label + ': unknown question type')
        else:
            current = order.index(kind)
            if current < previous:
                errors.append(label + ': question type order violation')
            previous = current
        score = number(q.get('points'), label)
        total += score
        if 'subpoints' in q:
            parts = q['subpoints']
            if not isinstance(parts, list) or not parts:
                errors.append(label + ': subpoints must be a nonempty list')
            elif sum((number(v, label + ' subpoint', False) for v in parts), Decimal(0)) != score:
                errors.append(label + ': subpoints do not equal points')
        source = q.get('source_kind')
        if source not in ['高考真题', '模拟题', '原创', '改编题']:
            errors.append(label + ': invalid source_kind')
        if data.get('require_real_sources') and source not in ['高考真题', '模拟题']:
            errors.append(label + ': real source required')
        if source in ['高考真题', '模拟题']:
            year = q.get('exam_year')
            if type(year) is not int:
                errors.append(label + ': exam_year must be an integer')
            elif source in ranges and not ranges[source][0] <= year <= ranges[source][1]:
                errors.append(label + ': exam year outside requested range')
            for field in ['source_question', 'exam_name', 'region']:
                if not isinstance(q.get(field), str) or not q[field].strip() or q[field] == '待核验':
                    errors.append(label + ': missing ' + field)
            url = q.get('source_url')
            try:
                parsed = urlparse(url) if isinstance(url, str) else None
                if parsed is None or parsed.scheme not in ['http', 'https'] or not parsed.netloc:
                    raise ValueError()
            except ValueError:
                errors.append(label + ': missing/invalid source_url')
            if q.get('verified') is not True:
                errors.append(label + ': source not marked verified')
            original = number(q.get('source_points'), label + ' source_points')
            if data.get('preserve_source_points') and original != score:
                errors.append(label + ': original points changed')
        elif source == '改编题':
            if not q.get('adapted_from') or not q.get('changes'):
                errors.append(label + ': adaptation attribution/changes required')
    if total != target:
        errors.append(f'total mismatch: {total} != {target}')
    return errors


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: python check_exam.py manifest.json')
        with Path(sys.argv[1]).open(encoding='utf-8-sig') as handle:
            problems = check(json.load(handle))
        print(json.dumps({'ok': not problems, 'errors': problems,
                          'limit': 'Structural checks only; no source or answer verification.'}, ensure_ascii=False, indent=2))
        sys.exit(1 if problems else 0)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'ok': False, 'errors': [str(exc)]}, ensure_ascii=False))
        sys.exit(1)
