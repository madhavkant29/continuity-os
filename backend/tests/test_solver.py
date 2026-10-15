from app.sample import demo_snapshot
from app.solver import analyze, solve, options


def test_refund_normal_is_feasible():
    result = analyze(demo_snapshot('enterprise-refund'), [])
    assert result['feasible']
    assert len(result['assignments']) == 3
    assert result['repair'] is None


def test_loss_of_approver_blocks_but_renewal_repairs():
    result = analyze(demo_snapshot('enterprise-refund'), ['p02'])
    assert not result['feasible']
    assert result['repair'] and result['repair']['feasible']
    assert result['repair']['renewals'] == [
        {'person_id':'p03','permission':'REFUND_APPROVE','type':'RENEW_EXPIRED_PERMISSION','cost':1}]
    assigns = {a['step_id'].split(':')[-1]:a['person_id'] for a in result['repair']['assignments']}
    assert assigns['approve'] != assigns['release']


def test_no_auto_grant_if_no_existing_permission():
    data = demo_snapshot('enterprise-refund')
    for p in data['people']:
        if p['id']=='p03':
            p['permissions'].clear()
    assert analyze(data, ['p02'])['repair'] is None


def test_separation_blocks_dual_role_person():
    data = demo_snapshot('enterprise-refund')
    result = solve(data, ['p02','p03'])
    assert not result['feasible']
    assert result['blockers'][0]['reason']=='POLICY_CONFLICT'


def test_all_unavailable_fails_closed():
    data = demo_snapshot('enterprise-refund')
    result = analyze(data, [p['id'] for p in data['people']])
    assert not result['feasible'] and result['repair'] is None


def test_skill_is_not_equivalent_to_authorization():
    data=demo_snapshot('enterprise-refund')
    eligible=options(data, ['p02'], False)
    approvals={c['person_id'] for c in eligible[1]}
    assert 'p03' not in approvals and 'p24' not in approvals


def test_multiple_workflows_have_valid_initial_assignments():
    for workflow in ('vendor-onboarding','production-hotfix','payroll-release','customer-data-export'):
        assert solve(demo_snapshot(workflow))['feasible']


def test_returned_assignments_respect_policy_for_all_workflows():
    for wid in ('enterprise-refund','vendor-onboarding','production-hotfix','payroll-release','customer-data-export'):
        data=demo_snapshot(wid)
        result=solve(data)
        assignments={a['step_id']:a['person_id'] for a in result['assignments']}
        assert all(assignments[a]!=assignments[b] for a,b in data['separation'])
