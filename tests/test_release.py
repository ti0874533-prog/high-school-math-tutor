"""Offline release checks. No network requests or student archive writes."""
import copy
import json
import re
import runpy
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'high-school-math-tutor'
CHECK = runpy.run_path(str(SKILL / 'scripts' / 'check_exam.py'), run_name='release_check')['check']


class ReleaseChecks(unittest.TestCase):
    def test_frontmatter_and_display_name(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        match = re.match(r'^---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', text)
        self.assertIsNotNone(match)
        self.assertEqual(match[1], 'high-school-math-tutor')
        self.assertLessEqual(len(match[2]), 1024)
        self.assertIn('# 家教备课出题助手', text)
        interface = (SKILL / 'agents' / 'openai.yaml').read_text(encoding='utf-8')
        self.assertIn('display_name: "家教备课出题助手"', interface)
        self.assertIn('allow_implicit_invocation: true', interface)

    def test_local_markdown_links(self):
        for p in ROOT.rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((p.parent / link.split('#')[0]).exists(), (p, link))

    def test_cloud_defaults_are_unconfigured(self):
        cfg = json.loads((SKILL / 'references' / 'archive-locations.json').read_text(encoding='utf-8'))
        self.assertEqual(cfg['status'], 'unconfigured')
        for key in ['private_config_file', 'local_root', 'primary_storage', 'drive_root_id', 'drive_root_url', 'local_workspace_config']:
            self.assertIsNone(cfg[key], key)
        self.assertIsNone(cfg['student_index']['file_id'])
        self.assertIsNone(cfg['student_index']['url'])
        self.assertFalse(cfg['automatic_sync'])

    def test_local_default_requires_user_configuration(self):
        cfg = json.loads((SKILL / 'references' / 'local-storage.json').read_text(encoding='utf-8'))
        self.assertEqual(cfg['status'], 'unconfigured')
        self.assertIsNone(cfg['workspace_config'])
        text = (SKILL / 'references' / 'local-storage.md').read_text(encoding='utf-8')
        self.assertIn('文字回答无须配置', text)
        self.assertIn('先确认输出目录', text)
        self.assertIn('外部配置文件所在目录为基准', text)

    def test_workspace_example_is_relative_and_offline(self):
        cfg = json.loads((ROOT / 'examples' / 'workspace.example.json').read_text(encoding='utf-8'))
        self.assertEqual(set(cfg['paths']), {'student_materials','question_bank','teaching_materials','generated','temporary','indexes','backups'})
        self.assertFalse(cfg['automatic_sync'])
        self.assertFalse(cfg['cloud_primary'])
        for value in list(cfg['paths'].values()) + [cfg['catalog'],cfg['workspace_root']]:
            self.assertFalse(Path(value).is_absolute())
            self.assertNotRegex(value, r'^[A-Za-z]:')

    def test_ten_templates_remain(self):
        self.assertEqual(len(list((SKILL / 'templates').glob('*.md'))), 10)

    def test_confirmation_and_data_boundaries_remain(self):
        core = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        rules = (SKILL / 'references' / 'archive-rules.md').read_text(encoding='utf-8')
        self.assertIn('不得自动删除档案、联系家长或其他第三方、申请家教订单', core)
        self.assertIn('用户明确确认具体版本后才写入', core)
        self.assertIn('提交前重读基线', rules)
        self.assertIn('没有权限就停止相关操作', rules)

    def test_search_policy_remains(self):
        text = (SKILL / 'references' / 'source-search-policy.md').read_text(encoding='utf-8')
        for phrase in ['小红书优先发现','广东深圳','北京、浙江模拟卷','实际考试年份＋省份＋学科','不得绕过登录、验证码或访问限制']:
            self.assertIn(phrase, text)

    def test_no_packaged_records_or_binary_artifacts(self):
        denied = {'.pdf','.docx','.xlsx','.png','.jpg','.jpeg','.zip','.pem','.key','.pyc'}
        for p in ROOT.rglob('*'):
            if p.is_file():
                self.assertNotIn(p.suffix.lower(), denied)
                self.assertFalse(p.name.endswith('.private.json'))
                self.assertNotEqual(p.name, '.env')

    def test_no_personal_locations_or_real_cloud_ids(self):
        for p in ROOT.rglob('*'):
            if p.is_file() and p.suffix in {'.md','.json','.yaml','.py'}:
                text = p.read_text(encoding='utf-8')
                self.assertNotRegex(text, r'(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s\n]+|/(?:Users|home)/[A-Za-z0-9_.-]+/')
                self.assertNotRegex(text, r'https://(?:drive|docs)\.google\.com/[^\s"<>]*[A-Za-z0-9_-]{25,}')
                self.assertNotRegex(text, r'gh[pousr]_[A-Za-z0-9]{20,}')

    def test_manifest_example_is_synthetic(self):
        data = json.loads((ROOT / 'examples' / 'exam-manifest.example.json').read_text(encoding='utf-8'))
        self.assertTrue(all(q['source_kind'] == '原创' for q in data['questions']))
        self.assertEqual(CHECK(data), [])

    def test_cli_example(self):
        result = subprocess.run([sys.executable,'-B',str(SKILL/'scripts'/'check_exam.py'),str(ROOT/'examples'/'exam-manifest.example.json')],capture_output=True,encoding='utf-8')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_wrong_total_rejected(self):
        data=json.loads((ROOT/'examples'/'exam-manifest.example.json').read_text(encoding='utf-8'))
        data['target_total']=6
        self.assertTrue(any('total mismatch' in e for e in CHECK(data)))

    def test_original_not_allowed_in_real_only_task(self):
        data=json.loads((ROOT/'examples'/'exam-manifest.example.json').read_text(encoding='utf-8'))
        data['require_real_sources']=True
        self.assertTrue(any('real source required' in e for e in CHECK(data)))

    def test_duplicate_ids_rejected(self):
        data=json.loads((ROOT/'examples'/'exam-manifest.example.json').read_text(encoding='utf-8'))
        data['questions'].append(copy.deepcopy(data['questions'][0]));data['target_total']=10
        self.assertTrue(any('duplicate' in e for e in CHECK(data)))

    def test_invalid_numbers_and_root_rejected(self):
        for value in [None, [], {'target_total': float('nan'),'type_order':['x'],'questions':[]}]:
            self.assertTrue(CHECK(value))


if __name__ == '__main__':
    unittest.main()
