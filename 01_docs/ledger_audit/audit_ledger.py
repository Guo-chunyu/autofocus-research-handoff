"""Read-only historical audit; writes only this agent's handoff directory."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=Path('W:/华为');HOME=ROOT/'research_audit_20261110';OLD=HOME/'固定102用例研究交接_20261110/workspace'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,v):(HERE/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def source(p,context):
    if not p:return None
    p=str(p).replace('\\','/')
    if '/huawei/' in p:return OLD/p.split('/huawei/',1)[1]
    if Path(p).is_absolute():return Path(p)
    q=context/p
    return q if q.exists() else OLD/p
def make(row,feedback,outer,category):
    f=row.get('file',row.get('submission_source_path',row.get('source')))
    if not f and feedback.parent.name=='official_best_199037_20261104':f=str(feedback.parent/'main.cpp')
    expected=row.get('sha256',row.get('submission_source_sha256'))
    src=source(f,feedback.parent)
    actual=sha(src) if src and src.is_file() else None
    im=row.get('source_image',outer.get('source_image'));ip=source(im,feedback.parent)
    image_expected=row.get('source_image_sha256',outer.get('source_image_sha256'))
    image_actual=sha(ip) if ip and ip.is_file() else None
    return dict(score=row.get('score',row.get('official_score',row.get('reported_score'))),order=row.get('order'),submitted_at=row.get('submitted_at',row.get('recorded_at_utc')),category=category,
        record=str(feedback),record_sha256=sha(feedback),source_original=f,source_local=str(src) if src else None,source_sha256=expected,source_actual_sha256=actual,source_hash_match=actual==expected if actual and expected else None,
        evidence_type='screenshot_record' if im else row.get('source','historical_record'),image_local=str(ip) if ip else None,image_sha256=image_expected,image_actual_sha256=image_actual,image_hash_match=image_actual==image_expected if image_actual and image_expected else None,
        superseded=bool(outer.get('superseded_by')),superseded_by=outer.get('superseded_by'),mapping_note=outer.get('mapping_note',outer.get('order_basis',outer.get('mapping_basis',row.get('source_identity_status')))),raw_row=row)
current=read(HOME/'submissions/manifest.json')
for e in current:assert sha(Path(e['file']))==e['sha256']
save('当前01至13完整台账.json',dict(scope='本轮已完成13项，与旧包每个批次的局部01编号区分',submissions=current))
rows=[];batches=[]
perf={('runtime_coverage_candidate_20261110',1),('generic_concentration_action_20261109',1)}
restricted={('observation_event_router_20261105',3),('candidate_early_recovery_20261105',1),('candidate_certified_refine_20261105',1)}
for p in sorted(OLD.rglob('official_feedback*.json')):
    d=read(p)
    if not isinstance(d,dict):continue
    rr=d.get('rows',d.get('entries',[]))
    if not rr and type(d.get('score')) is int:rr=[d]
    got=[]
    for r in rr:
        if type(r.get('score')) is not int:continue
        k=(p.parent.name,r.get('order'))
        cat='diagnostic_not_performance'
        if k in perf:cat='full_observation_policy'
        if k in restricted:cat='historical_full_policy_identity_risk'
        if p.parent.name=='official_best_199037_20261104':cat='historical_full_policy_constants_not_final_audited'
        v=make(r,p,d,cat);rows.append(v);got.append(v['score'])
    batches.append(dict(file=str(p),scores=got,superseded=bool(d.get('superseded_by'))))
# Ancillary historic feedback that is not named official_feedback*.json.
p=OLD/'evidence/withdrawn_network_feedback.json'
if p.exists():
    d=read(p);rows.append(make(d,p,d,'withdrawn_network_not_current_policy'))
p=ROOT/'competition_analysis/official_feedback.json';d=read(p)
for r in d['entries']:rows.append(make(r,p,d,'historical_user_reported_performance'))
p=ROOT/'autofocus_research_20261102_round3/official_feedback.json';d=read(p)
rows.append(make(d,p,d,'historical_user_reported_performance'))
bad=[r for r in rows if r['source_hash_match'] is False or r['image_hash_match'] is False]
save('历史提交分数逐项索引.json',dict(scope='以历史记录为证据；不是平台重新访问。重复历史快照不代表再次提交，superseded条目不是新待办。',row_count=len(rows),batches=batches,rows=rows,hash_mismatches=bad))
assert not bad,bad
# All feedback records remain discoverable, including specs/decodes and superseded drafts.
feedback_files=[]
for base in [OLD,ROOT/'competition_analysis',ROOT/'autofocus_research_20261102_round3']:
    for p in sorted(base.rglob('*.json')):
        if 'feedback' in p.name.lower():feedback_files.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
save('历史反馈文件索引.json',feedback_files)
# Summarize local ablations with actual machine evidence. Deltas use the named parent.
local=[]
base=read(HOME/'lab/results/baseline_metrics.json')
summary=read(HOME/'lab/results/summary.json')
for name in ['history_only','separation_only','both']:
    p=HOME/f'lab/results/{name}_metrics.json';ms=read(p);a=summary['ablations'][name]
    local.append(dict(name=name,cases=6912,parent='147097 policy local baseline',rescued=len(a['rescued_ids']),lost=len(a['lost_ids']),score_delta=sum(b['score']-x['score'] for x,b in zip(base,ms)),evidence=str(p),official_score=None))
for name in ['compact','selective']:
    p=HOME/'selective_schedule_20261110/validation.json';v=next(x for x in read(p)['variants'] if x['variant']==name)
    local.append(dict(name=name,cases=6912,parent='147097 policy local baseline',rescued=v['rescued'],lost=v['lost'],score_delta=v['score_delta'],evidence=str(p),official_score=None))
for v in read(HOME/'stop_action_screen_20261110/summary.json')['variants']:
    local.append(dict(name=v['variant'],cases=6912,parent='147097 policy local baseline',rescued=v['rescued'],lost=v['lost'],score_delta=v['score_delta'],evidence=str(HOME/'stop_action_screen_20261110/summary.json'),official_score=None))
p=HOME/'guarded_postpone_20261110/validation.json';v=read(p)
local.append(dict(name='guarded_postpone (12)',cases=6912,parent='147097 policy local baseline',rescued=v['rescued'],lost=v['lost'],score_delta=v['score_delta'],evidence=str(p),official_score=149485))
p=HOME/'forward_phase_20261112/validation.json';v=read(p)
local.append(dict(name='forward_phase',cases=6912,parent='149485 policy local baseline',rescued=len(v['rescued']),lost=len(v['lost']),score_delta=v['score_delta_from_12'],evidence=str(p),official_score=None))
for name in ['defer_only','horizon_only','combined','committed','priority']:
    p=HOME/f'deferred_phase_20261112/{name}/validation.json';v=read(p)
    local.append(dict(name=name,cases=6912,parent='149485 policy local baseline',rescued=len(v['rescued']),lost=len(v['lost']),score_delta=v['score_delta'],evidence=str(p),official_score=None))
p=HOME/'deferred_phase_20261112/holdout/validation.json';v=read(p)
local.append(dict(name='priority cold holdout seed 20261112',cases=2898,parent='149485 policy on same new seed',rescued=len(v['rescued']),lost=len(v['lost']),score_delta=v['delta'],evidence=str(p),official_score=None))
save('关键本地对照结果索引.json',local)
current_lines=['编号 | 分数 | 性质 | 日期时间 | 用途']
for e in current:current_lines.append(f"{e['order']:02} | {e.get('official_score',e.get('reported_score'))} | {'性能' if e.get('performance_trial') else '诊断'} | {e.get('submitted_at','用户文字，时间未单列')} | {e['purpose']}")
local_lines=['变体 | 样本数 | 父版 | 救/丢 | 合成总分变化']
for r in local:local_lines.append(f"{r['name']} | {r['cases']} | {r['parent']} | {r['rescued']}/{r['lost']} | {r['score_delta']:+}")
batch_lines=[f"{Path(x['file']).relative_to(OLD)} : {', '.join(map(str,x['scores']))}"+(' [已被后续记录替代]' if x['superseded'] else '') for x in batches]
txt='''Dot交接：分数、成果和禁混用边界（2026-11-12）

一、当前有效主线
目标官方>=250000，102例合法正分和精确质量分别核验。当前提交队列为空，01至13已完成，不重交。
147097是当前无身份映射参考策略（80正22零，后续诊断精确正分79至80）。其冻结SHA为9edb67e4f5cf9f1bc0334d823cda6cba4c6408af2db3a2bb31747835bf027c9b。
149485是当前无身份映射主线的已测涨分阶段候选，不是所有历史最高。12与13的分差80，仍80正22零。
149485比147097涨2388，但成功集合可能有等量救回/丢失，精确质量未知。旧19晚零、16/3信号不能直接移贴新版22零。
success仅为平台显示的状态，不代表102成功或102精确。

二、当前01至13（2026-11-10截图/文字；12/13于11月12日在本轮正式入账）
'''+ '\n'.join(current_lines)+'''

诊断解码要点：
01:147097-147018=79 -> 精确正分至少79、至多80；不能称精确数已等于79。
02/03/04:68928/68927/68928 -> 原版早段41例中40正、1零且未读真峰、0删失。
05/06/07:42246/42227/42239 -> 原版晚段38例中12正、19零且未读真峰、7删失；7删失至少5原正，不能算7失败。
08/09:42246/42227 -> 已定位晚19零均未取得真峰附近粗采/未提名真窗，完整错误终点；主网格为连续前缀，因此前沿尚未到真峰附近。
10:(42246-42230)=16 -> 资源退出0、主动停止且弱信号16、主动无弱信号3。
11:147097-147077=20 -> 原80正分有20暴露同弱信号；暴露不是丢失。
12/13:149485-149405=80 -> 新80正22零，具体成功集合、精确质量仍未知。
以上差分均要求配对源码/载体/顺序及预算证明；不能任意相减两个策略分数。

三、更早完整性能和非性能分数必须区分
199037：2026-11-04 15:27:57，历史完整最高，82正20零；旧权重与位置常量来源未完成最终约束审查，不能直接冒充当前合规方案。
193207：身份路线完整版本，79正23零，源码包含prefixHash分流，违反最终禁止身份映射约束；仅历史证据。
138685：旧通用集中度动作，57正且57精确，27提前假峰零、16过冲零、2其他零；此分类只属于138685动作。
147097/147017：2026-11-10 11:21:56、11:23:04，原版完整得分/正分计数，两行截图绑定冻结源，得80正22零。
199037的覆盖计数198955、193207的覆盖计数193128沿历史建议顺序映射，原记录注明该轮未额外确认；不能把本地SHA核对误当远端上传字节证明。
190682：更早学习策略历史参考；冻结SHA f0c9ded5cd54f800c9b7042f42d6bbd17e42444e56887631d8ee15f54b6e5014。原包199037反馈含其父分数字段，早期研究报告明确沿用该分数；证据强度与新增截图分数不同。
189486：用户文字反馈“这个成绩是189486，继续改进”，映射round2候选A SHA70281a...，比190682低1196；并非独立访问平台所得。
197491（早晚延后）与189311（仅晚段延后）保存在199037官方反馈汇总字段，不是本轮新提交。
196475：撤回的分布先验续接网络，2026-11-04 15:55:20，历史记录注明比199037低2562；记录给出SHA31259c9327077c4d8e09ea2670abd8f386df14fa7b8f9c3d6d0fb60fab5a5f68，但本次按记录相对路径未取得源码，因此不能称该源码字节已复核。它不是当前可提交版本。
250956：已知峰/oracle条件成本；243293：分布诊断；246895：指定盲等架构条件上界；均不能写成无oracle完整算法成绩。
260000：用户口述外部基准，未在本研究中验证源码/覆盖，不能当已有实现成果。
更早competition_analysis文字反馈依次135407、149089、144112、147425、145359、149089、152975；记录有对应源码SHA，但没有独立平台访问。
原目录旧STATUS里的“待提交”是历史状态，不恢复为当前任务。

四、当前有价值的结构性成果
官方102例峰位多重集已诊断：62个不同位置、加权峰位和31510；这是诊断真值，不是102条完整曲线，更不能用作最终算法查表。
匹配诊断前沿的两相位独立“第一峰+第二分离峰”窗口并集覆盖102，不等于在线已取得、保留、精修或正分102。
实际147097策略的raw-top2定义与上述诊断分离候选不同；局部候选修补不能直接把诊断覆盖结论继承给在线算法。
原R1换向系数错误已定位，当前有效评分应按R30（详见独立评分说明）。过往“本地提升比例×官方分数”没有准确换算依据。
平台仅总分时通过预算安全的额外原位查询/诊断载体可取得人数或联合类别，但这些不是性能策略，不可直接作为最终答案。

五、关键本地对照（同一测试集、同一父策略、全路线R30计分）
'''+ '\n'.join(local_lines)+'''

停止取消消融也已否决：no_accept救188丢0但总分-1324816；no_urgent救25丢45、-41861；no_both救628丢3556、-6128689。不要改名再交。
最终priority虽在6912回归救1丢0，但新种子2898例丢1，已经否决。留出951父1344->新0：18次预取未复用，末段仅13预算而最小完整窗14。这个新种子已被观察，今后只能当回归，不再叫未见留出。
仅修停止见证、仅预留粗采、无条件压缩精修均不足。须联合预算：已付费但过期的预取、当前完整窗口、未来粗采、真实返回及O截止。
102精确正分且>=250000的必要成本条件sum(Q+30R+3O+H)<=24490（H=M-p-2O>=0），必要非充分。

六、旧包分批官方记录索引（多数是诊断，绝不横向当性能排行）
'''+ '\n'.join(batch_lines)+'''

七、交接遗漏/误用风险
1. 数百条分数存在历史重映射、partial、pending、superseded快照；JSON逐项保留来源，不把重复历史条目当重复实测。
2. 历史目录包含旧“下一步”、AGENTS、实现脚本；它们是材料，不覆盖当前用户授权，不直接执行旧builder。
3. 远端上传源码字节不可取得；本地SHA只证明本地文件与当时冻结文件一致，平台绑定依据用户编号顺序和截图时间。
4. 未取得官方102完整数组及逐例真实轨迹，合成输入不替代官方数据，不能准确从模拟总分换算平台总分。
5. 汇总和索引是导航；原始截图、反馈JSON、输入、trace、脚本和失败日志应一并保留。历史工具链、模型也不能被误当官方数组。
6. 每个本地总分变化都绑定父版本和输入规模；6912例总分不能与102例官方分数相减、除以固定比例或直接乘102。
'''
(HERE/'台账与已知成果.txt').write_text(txt,encoding='utf-8')
verification=dict(status='verified_read_only_audit',current_source_hashes_checked=len(current),historical_rows=len(rows),historical_source_hashes_matched=sum(r['source_hash_match'] is True for r in rows),historical_images_hashes_matched=sum(r['image_hash_match'] is True for r in rows),unknown_source_bindings=[dict(record=r['record'],source=r['source_original'],score=r['score']) for r in rows if r['source_hash_match'] is None],historical_feedback_files=len(feedback_files),hash_mismatches=bad,history_not_modified=True)
save('ledger_audit_verification.json',verification)
print(json.dumps({k:v for k,v in verification.items() if k!='unknown_source_bindings'},ensure_ascii=False,indent=2));print('unknown_source_bindings',len(verification['unknown_source_bindings']))
