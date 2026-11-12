"""Run python -m unittest discover -s 02_tools -p 'test_*.py'."""
import unittest
from score_trace import score_trace

class ScoringTests(unittest.TestCase):
    def values(self,p,n=400):
        v=[0]*n;v[p]=1000;return v
    def test_R30(self):
        m=score_trace(self.values(1),[0,8,1]);self.assertEqual(m['score'],2945);self.assertEqual(m['R'],1)
    def test_query_boundary(self):
        v=self.values(200);self.assertEqual(score_trace(v,[200]*199)['score'],2601);self.assertEqual(score_trace(v,[200]*200)['score'],0)
    def test_distance_boundary(self):
        v=self.values(200);self.assertEqual(score_trace(v,[203])['score'],2193);self.assertEqual(score_trace(v,[204])['score'],0)
    def test_overshoot(self):
        v=self.values(0);self.assertEqual(score_trace(v,[199,0])['score'],2371);self.assertEqual(score_trace(v,[200,0])['score'],0)
    def test_turns(self):
        v=self.values(0);self.assertEqual(score_trace(v,[0,1,0,1,0,1,0,1,1])['R'],6);self.assertEqual(score_trace(v,[1,0,1,0,1,0,1,0])['score'],0)
    def test_stationary(self):
        self.assertEqual(score_trace(self.values(1),[1,1,0,0,1])['R'],2)
    def test_tie(self):
        v=self.values(199);v[200]=1000;self.assertEqual(score_trace(v,[200,199])['target'],199)
        v=self.values(199,401);v[201]=1000;self.assertEqual(score_trace(v,[201,199])['target'],199)
    def test_one_point_becomes_zero(self):
        v=self.values(900,1000);t=[900,0,920]+[920]*145+[900]
        self.assertEqual(score_trace(v,t)['score'],1);self.assertEqual(score_trace(v,t+[900])['score'],0)
    def test_invalid_trace(self):
        for t in [[],[-1],[400],[1.5],[True]]:
            with self.assertRaises(ValueError):score_trace(self.values(1),t)
    def test_R1_is_not_ratio(self):
        v=self.values(1);m=score_trace(v,[0,8,1]);self.assertEqual(m['legacy_R1_score']-m['score'],29)
    def test_soft_clipping(self):
        v=self.values(900,1000);m=score_trace(v,[900,0,920]+[920]*146+[900]);self.assertEqual(m['score'],0)

if __name__=='__main__':unittest.main()
