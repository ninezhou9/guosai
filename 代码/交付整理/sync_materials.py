"""Maintain the appendix, source snapshot, package and project navigation."""
from pathlib import Path
from datetime import datetime
import ast,copy,hashlib,io,json,os,shutil,sys,tokenize,zipfile

ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'论文写作/附录与支撑材料_20260913'
WORK=ROOT/'代码/交付整理/缓存'
SUPPORT=WORK/'支撑材料'
REFILL=ROOT/'代码/结果导出/缓存'
NAMES=['result1.xlsx','result2.xlsx','result3.xlsx','result4-2.xlsx','result4-3.xlsx']
STEM='论文附录'
SOURCE_GROUPS={
    '':('q1_solution.py',),
    '实验/q2_fresh_20260912':('fresh_engine.py','run_fresh.py','write_report.py','requirements.txt'),
    '实验/q3_revision_a_20260912':('q3_engine.py','run_q3.py','deliver_q3.py'),
    '实验/q4_independent_codex_20260912':('model.py','run.py','deliver.py'),
}


def final_source_paths():
    """Only the final model versions and their current support tools enter the ZIP."""
    return [Path('代码')/folder/name for folder,names in SOURCE_GROUPS.items() for name in names]


def packaged_source_path(rel):
    rel=Path(rel)
    if rel.name=='README.md' and rel.parent==Path('代码'):return rel
    text=rel.as_posix()
    groups={'代码/实验/q2_fresh_20260912/':'问题二','代码/实验/q3_revision_a_20260912/':'问题三',
            '代码/实验/q4_independent_codex_20260912/':'问题四','代码/结果导出/':'时间对齐',
            '代码/matlab/':'绘图','代码/figures/论文数据图/问题三/':'绘图'}
    for prefix,folder in groups.items():
        if text.startswith(prefix):return Path('代码')/folder/rel.name
    assert rel.parent==Path('代码'),rel
    return Path('代码/问题一')/rel.name


def packaged_source_bytes(rel):
    """Adapt paths and removed standalone-check dependencies, preserving solvers."""
    rel=Path(rel);raw=(ROOT/rel).read_bytes();text=raw.decode('utf-8-sig');original=text
    if rel==Path('代码/README.md'):
        text='''# 最终代码入口

| 目录 | 入口 |
| --- | --- |
| 问题一 | q1_solution.py |
| 问题二 | run_fresh.py；依赖见requirements.txt |
| 问题三 | run_q3.py、deliver_q3.py |
| 问题四 | run.py、deliver.py、audit.py |
| 时间对齐 | boundary_prediction.py、prepare_templates.py、refill_templates.mjs、verify_templates.py |
| 绘图 | run_all_figures.m、figA_netload_forecast_update.py |

各问仅保留最终实现及其核验程序。先将题目原始基础数据目录放在支撑材料根目录，再按第一至四问顺序计算，最后运行时间对齐程序。首次完整计算需要生成各问预测与调度缓存，缓存未打包。已交付答案直接读取结果目录的五份result文件。

支撑包副本只适配目录路径，求解函数、参数和计算方法保持不变。各问直接生成的结果仍是自然日口径，完成时间对齐后才与最终模板展示窗口一致。完整命令和新增边界假设见根目录使用说明.md。
'''
    else:
        mappings=[('代码/实验/q2_fresh_20260912','代码/问题二'),('代码/实验/q3_revision_a_20260912','代码/问题三'),
          ('代码/实验/q4_independent_codex_20260912','代码/问题四'),('代码/results/q1','代码/问题一/results'),
          ('代码/q1_solution.py','代码/问题一/q1_solution.py'),('代码/figures/q1','结果/图表/问题一'),
          ('q2_fresh_20260912','问题二'),('q3_revision_a_20260912','问题三'),('q4_independent_codex_20260912','问题四')]
        for old,new in mappings:text=text.replace(old,new)
        if '实验' in rel.parts:
            text=text.replace('BASE.parents[2]','BASE.parents[1]')
        if rel==Path('代码/q1_solution.py'):
            text=text.replace('ROOT = Path(__file__).resolve().parents[1]','ROOT = Path(__file__).resolve().parents[2]')
        if rel.suffix=='.m':
            text=text.replace("ROOT = 'C:\\Users\\sss\\Desktop\\国赛';","ROOT = fileparts(fileparts(fileparts(mfilename('fullpath'))));")
            text=text.replace("fullfile(ROOT,'代码','figures','论文数据图')","fullfile(ROOT,'结果','图表')")
        if rel==Path('代码/实验/q3_revision_a_20260912/run_q3.py'):
            text=text.replace('from check_engine import checks\n','')
            text=text.replace("['q3_engine.py','check_engine.py','run_q3.py']","['q3_engine.py','run_q3.py']")
            text=text.replace("        result=checks(y,p,load,f,pred);dump(out/'engine_checks.json',result)\n",'')
        if rel==Path('代码/实验/q4_independent_codex_20260912/run.py'):
            helper=core_excerpt(ROOT/'代码/实验/q4_independent_codex_20260912/test_model.py',['physical'])
            text=text.replace('from test_model import physical',helper)
        if rel==Path('代码/实验/q4_independent_codex_20260912/deliver.py'):
            text=text.replace("; checks=json.loads((OUT/'audit.json').read_text(encoding='utf-8')) if (OUT/'audit.json').exists() else None",'')
            text=text.replace("    unit=json.loads((m.BASE/'tests/unit_checks.json').read_text(encoding='utf-8'))\n",'')
            text=text.replace("        f'单元与因果检查 {unit[\"passed\"]}/{unit[\"total\"]} 通过。',\n",'')
            text=text.replace("        f'独立全年与交付审核：{checks[\"passed\"]}/{checks[\"total\"]} 通过。' if checks else '独立全年与交付审核：待执行。','',\n",'')
            recovery_start=text.index("    recovery=m.BASE/'tests/recovery_checks.json'")
            recovery_end=text.index("    q3=json.loads((m.Q3/'summary.json')",recovery_start)
            text=text[:recovery_start]+text[recovery_end:]
            text=text.replace("[OUT,m.BASE/'figures',m.BASE/'tests']","[OUT,m.BASE/'figures']")
            text=text.replace('python -X utf8 test_model.py → python -X utf8 run.py --jobs 9 → python -X utf8 deliver.py --sensitivity → python -X utf8 audit.py',
                              'python -X utf8 run.py --jobs 9 → python -X utf8 deliver.py --sensitivity')
            text=text.replace('python -X utf8 test_model.py; python -X utf8 run.py --jobs 9; python -X utf8 deliver.py --sensitivity; python -X utf8 audit.py',
                              'python -X utf8 run.py --jobs 9; python -X utf8 deliver.py --sensitivity')
    return raw if text==original else text.encode('utf-8')


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def core_excerpt(path,names):
    source=path.read_text(encoding='utf-8-sig');lines=source.splitlines();parts=[]
    for node in ast.parse(source).body:
        if isinstance(node,ast.FunctionDef) and node.name in names:
            raw='\n'.join(lines[node.lineno-1:node.end_lineno])
            tokens=[t for t in tokenize.generate_tokens(io.StringIO(raw).readline) if t.type!=tokenize.COMMENT]
            raw=tokenize.untokenize(tokens);fn=ast.parse(raw).body[0]
            if isinstance(fn.body[0],ast.Expr) and isinstance(fn.body[0].value,ast.Constant) and isinstance(fn.body[0].value.value,str):
                rows=raw.splitlines();del rows[fn.body[0].lineno-1:fn.body[0].end_lineno];raw='\n'.join(rows)
            parts.append('\n'.join(x.rstrip() for x in raw.splitlines() if x.strip()))
    assert len(parts)==len(names),(path,names)
    return '\n\n'.join(parts)


def build():
    from docx import Document
    from docx.shared import Pt,RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    WORK.mkdir(parents=True,exist_ok=True)
    baseline=PACKAGE/(STEM+'.docx')
    assert baseline.is_file(), 'Current appendix is required as the formatting template'
    doc=Document(baseline)
    code_sample=next(p for p in doc.paragraphs if p.text.startswith('def solve('))
    code_properties=copy.deepcopy(code_sample._p.pPr)
    # Keep the supplied section geometry and document styles.
    for p in list(doc.paragraphs):p._element.getparent().remove(p._element)
    ai_text='本参赛队在竞赛过程中使用了 ChatGPT，主要用于代码检查与调试、基于 MATLAB 的科研绘图与结果可视化；参赛队已人工讨论并修改建模方案，并核验代码。详见支撑文件。'
    items=[('h2','AI工具使用声明'),('p',ai_text),('break',''),('h1','附录'),('h2','A 支撑文件列表'),
      ('p','1. AI使用说明.docx'),
      ('p','2. 代码/：问题一至四的最终模型。'),
      ('p','3. 结果/：result1.xlsx、result2.xlsx、result3.xlsx、result4-2.xlsx、result4-3.xlsx。'),
      ('break',''),('h2','B 核心源码'),
      ('p','以下列出四问的主要计算函数。')]
    specs=[('问题一','代码/q1_solution.py',['solve']),
      ('问题二','代码/实验/q2_fresh_20260912/fresh_engine.py',['plan_lp','action']),
      ('问题三','代码/实验/q3_revision_a_20260912/q3_engine.py',['bellman_batch']),
      ('问题四','代码/实验/q4_independent_codex_20260912/model.py',['bellman'])]
    excerpts=[]
    for i,(title,rel,names) in enumerate(specs):
        if i in [2,4]:items.append(('break',''))
        code=core_excerpt(ROOT/rel,names)
        packaged=packaged_source_path(rel).as_posix()
        items.extend([('h3',title),('code',code)])
        excerpts.append(dict(section=title,source=rel,packaged_source=packaged,functions=names,source_sha256=digest(ROOT/rel),code=code))
    b=json.loads((REFILL/'boundary_prediction.json').read_text(encoding='utf-8'))
    items.extend([('break',''),('h2','C 时间口径与跨日计算'),
      ('p','输入时标按十分钟区间的结束时刻解释，例如0:10表示00:00—00:10。结果模板时间栏保持原样，首段00:10—00:20对应模型第二段，末段对应次日00:00—00:10；末段不能直接用当天第一段替代。'),
      ('p',f'第一问的新增边界假设是光伏预测曲线延续一个日周期，电价和负载按题设每日重复。调用原求解器重新计算下一周期，并校验其期初储电量与前一期末相接。次日首段购电量为{b["q1"]["first_slot_kwh"]:.4f} kWh，储电衔接值为{b["q1"]["day_initial_kwh"]:.4f} kWh；该值依赖日周期延拓假设。'),
      ('p',f'第二问与4-2沿用原预测和优化方法向后补算，2026年1月1日首段为{b["first_slot_kwh"]:.4f} kWh。第三问与4-3沿用2025年12月31日18点预报覆盖次日1—18点，对19—24点采用此前7天零点发布的同一时刻预报均值延拓，再执行原插值、历史残差校准及优化，首段为{b["q3"]["first_slot_kwh"]:.4f} kWh。延拓预报不是附件中实际发布的新预报，也不是实际观测。'),
      ('p','购电表合计覆盖模板展示的00:10—次日00:10，充放电和紧急购电仍按各自模板指定的自然日统计；原论文全年费用对应自然日范围，二者不能直接混用。每行末段接入次日零点产生的计划，不将其表述为前一日零点已知的决策。4-2和4-3年末跨日费用采用预测电价。')])
    markdown=[]
    for kind,text in items:
        if kind=='break':doc.add_page_break();continue
        if kind.startswith('h'):
            level=int(kind[1]);p=doc.add_heading(text,level)
            for run in p.runs:run.font.color.rgb=RGBColor(0,0,0)
            markdown.extend(['#'*level+' '+text,''])
        elif kind=='code':
            for line in text.splitlines():
                p=doc.add_paragraph()
                if code_properties is not None:p._p.insert(0,copy.deepcopy(code_properties))
                p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
                p.paragraph_format.line_spacing=Pt(10)
                run=p.add_run(line);run.font.name='Consolas';run.font.size=Pt(8)
                fonts=run._element.get_or_add_rPr().rFonts
                fonts.set(qn('w:eastAsia'),'宋体')
            markdown.extend(['```python',text,'```',''])
        else:doc.add_paragraph(text);markdown.extend([text,''])
    doc.save(WORK/(STEM+'.docx'))
    (WORK/(STEM+'.md')).write_text('\n'.join(markdown),encoding='utf-8')
    ai=Document(SUPPORT/'AI使用说明.docx')
    ai.paragraphs[2].text='本参赛队在竞赛过程中使用 ChatGPT（OpenAI）辅助开展代码检查与调试、基于 MATLAB 的科研绘图与结果可视化。'
    for p in list(ai.paragraphs):
        if p.text.startswith('在结果整理环节，借助 ChatGPT'):
            p._element.getparent().remove(p._element)
    ai.save(WORK/'AI使用说明.docx')
    check=Document(WORK/(STEM+'.docx'))
    actual='\n'.join(p.text for p in check.paragraphs)
    for e in excerpts:assert e['code'] in actual,e['source']
    assert len(check.tables)==0
    (WORK/'document_content_checks.json').write_text(json.dumps(dict(status='content_verified_render_pending',excerpts=excerpts,paragraphs=len(check.paragraphs),tables=0,baseline=str(baseline)),ensure_ascii=False,indent=2),encoding='utf-8')
    # This PDF is an independent layout of the same items, not a Word export.
    render_pdf(items,WORK/(STEM+'.pdf'))
    ai_items=[('h1' if p.style.name=='Heading 1' else 'h2' if p.style.name=='Heading 2' else 'p',p.text) for p in ai.paragraphs if p.text]
    render_pdf(ai_items,WORK/'AI使用说明_核对.pdf')
    print(json.dumps({'docx_built':2,'appendix_paragraphs':len(check.paragraphs),'core_sources':[e['source'] for e in excerpts],'pdf_renderer':'independent ReportLab layout; not a DOCX render'},ensure_ascii=False))


def render_pdf(items,path):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Preformatted,KeepTogether
    from xml.sax.saxutils import escape
    pdfmetrics.registerFont(TTFont('Song','C:/Windows/Fonts/simsun.ttc',subfontIndex=0))
    pdfmetrics.registerFont(TTFont('Hei','C:/Windows/Fonts/simhei.ttf'))
    pdfmetrics.registerFont(TTFont('Code','C:/Windows/Fonts/consola.ttf'))
    body=ParagraphStyle('body',fontName='Song',fontSize=10.5,leading=16,spaceAfter=6)
    headings={k:ParagraphStyle(k,fontName='Hei',fontSize=size,leading=size+5,spaceBefore=8,spaceAfter=6,keepWithNext=True) for k,size in [('h1',15),('h2',12),('h3',11)]}
    code=ParagraphStyle('code',fontName='Code',fontSize=7.6,leading=10,spaceAfter=0)
    story=[]
    for kind,text in items:
        if kind=='break':story.append(PageBreak())
        elif kind=='code':
            for line in text.splitlines():
                while pdfmetrics.stringWidth(line,'Code',7.6)>430:
                    n=len(line)
                    while pdfmetrics.stringWidth(line[:n],'Code',7.6)>430:n-=1
                    split=line.rfind(' ',0,n)
                    if split<max(10,n//2):split=n
                    story.append(Preformatted(line[:split],code));line='    '+line[split:].lstrip()
                story.append(Preformatted(line or ' ',code))
        else:story.append(Paragraph(escape(text),headings.get(kind,body)))
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=70,rightMargin=70,topMargin=50,bottomMargin=50).build(story)


def sync_files():
    WORK.mkdir(parents=True,exist_ok=True)
    backup=WORK/'备份'/datetime.now().strftime('%Y%m%d_%H%M%S')
    backup.mkdir(parents=True,exist_ok=False)
    before={}
    def write_target(src,target):
        assert target.resolve().is_relative_to(ROOT.resolve())
        if target.exists() and digest(src)!=digest(target):
            dest=backup/target.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,dest)
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
        assert digest(src)==digest(target)
    archive=PACKAGE/'支撑材料.zip'
    old_archive=backup/'支撑材料_更新前.zip';shutil.copy2(archive,old_archive)
    for name in NAMES:
        source=REFILL/'filled'/name
        assert digest(source)==next(x['sha256'] for x in json.loads((REFILL/'verification.json').read_text(encoding='utf-8'))['verified'] if x['file']==name)
        write_target(source,SUPPORT/'结果'/name)
    copied={};package_hashes={};source_map={}
    for rel in final_source_paths():
        source=ROOT/rel
        assert source.is_file(),('Missing final source',source)
        assert source.resolve().is_relative_to((ROOT/'代码').resolve())
        packaged=packaged_source_path(rel)
        transformed=WORK/'source_staging'/packaged
        transformed.parent.mkdir(parents=True,exist_ok=True)
        transformed.write_bytes(packaged_source_bytes(rel))
        target=SUPPORT/packaged
        write_target(transformed,target);copied[str(rel)]=digest(source)
        package_hashes[packaged.as_posix()]=digest(target);source_map[str(rel)]=packaged.as_posix()
    if '--include-documents' in sys.argv:
        for name in [STEM+'.docx']:
            write_target(WORK/name,PACKAGE/name)
        write_target(WORK/'AI使用说明.docx',SUPPORT/'AI使用说明.docx')
    (WORK/'sync_state.json').write_text(json.dumps(dict(backup=str(backup),source_hashes=copied,packaged_source_hashes=package_hashes,source_map=source_map),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(synced_source_and_readme_files=len(copied),backup=str(backup)),ensure_ascii=False))


def pack(candidate=False):
    state=json.loads((WORK/'sync_state.json').read_text(encoding='utf-8'))
    sources=state['source_hashes']
    selected={str(rel) for rel in final_source_paths()}
    assert set(sources)==selected,('Source manifest does not match final versions',set(sources)^selected)
    selected_packaged={packaged_source_path(rel).as_posix() for rel in final_source_paths()}
    packaged_sources={p.relative_to(SUPPORT).as_posix() for p in (SUPPORT/'代码').rglob('*') if p.is_file()}
    assert packaged_sources==selected_packaged,('Unexpected or missing packaged source',packaged_sources^selected_packaged)
    assert not (SUPPORT/'源码').exists(),'Old nested source directory still exists'
    for rel,h in sources.items():
        target=SUPPORT/state['source_map'][rel]
        assert digest(ROOT/rel)==h and target.read_bytes()==packaged_source_bytes(rel)
    entries={p.relative_to(SUPPORT).as_posix():p for p in SUPPORT.rglob('*') if p.is_file() and not p.name.startswith('~$')}
    expected_entries=selected_packaged|{'AI使用说明.docx'}|{'结果/'+n for n in NAMES}
    assert set(entries)==expected_entries,('Unexpected or missing support file',set(entries)^expected_entries)
    if candidate:entries['AI使用说明.docx']=WORK/'AI使用说明.docx'
    target=WORK/('支撑材料_待Word分页核验.zip' if candidate else '支撑材料_同步.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,p in sorted(entries.items()):z.write(p,name)
    with zipfile.ZipFile(target) as z:
        assert set(z.namelist())==set(entries) and z.testzip() is None
        for name,p in entries.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest(p)
    if not candidate:
        for name in [STEM+'.docx']:
            assert digest(PACKAGE/name)==digest(WORK/name),('Document not synchronized',name)
        assert digest(SUPPORT/'AI使用说明.docx')==digest(WORK/'AI使用说明.docx')
        shutil.copy2(target,PACKAGE/'支撑材料.zip')
    from pypdf import PdfReader
    appendix=WORK/(STEM+'.pdf')
    audit=WORK/('候选包核验' if candidate else '核验');audit.mkdir(exist_ok=True)
    size=dict(limit_bytes=20000000,support_zip_bytes=target.stat().st_size,appendix_pdf_bytes=appendix.stat().st_size,
      appendix_pdf_pages=len(PdfReader(appendix).pages),remaining_full_paper_pdf_bytes=20000000-target.stat().st_size,
      remaining_body_without_appendix_bytes=20000000-target.stat().st_size-appendix.stat().st_size)
    (audit/'体积核验.json').write_text(json.dumps(size,ensure_ascii=False,indent=2),encoding='utf-8')
    doc_checks=json.loads((WORK/'document_content_checks.json').read_text(encoding='utf-8'))
    report=dict(status='prepared_awaiting_word_pagination_review' if candidate else 'synchronized',archive_files=len(entries),source_and_readme_files=len(sources),
        code_files=sum(Path(p).suffix.lower() in ['.py','.m','.ps1','.mjs','.js'] for p in sources),
        archive_sha256=digest(target),source_hashes=sources,
        packaged_source_hashes=state['packaged_source_hashes'],source_map=state['source_map'],
        code_excerpts_verified=[{k:v for k,v in e.items() if k!='code'} for e in doc_checks['excerpts']],
        word_render_status='not_verified',pdf_render_status='independent layout verified separately',
        result_hashes={n:digest(SUPPORT/'结果'/n) for n in NAMES},backup=state['backup'])
    (audit/'交付核验记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=report['status'],archive_files=len(entries),source_and_readme_files=len(sources),code_files=report['code_files'],size=size),ensure_ascii=False))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    {'build':build,'sync':sync_files,'prepare-package':lambda:pack(candidate=True),'pack':pack}[sys.argv[1]]()
