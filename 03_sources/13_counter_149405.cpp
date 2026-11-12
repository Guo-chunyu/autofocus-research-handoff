// EXPERIMENTAL ONLINE SCHEDULING ONLY. No oracle/identity/peak table.
#define COUNT_QUERY 1
// A fresh observation-only policy. No case identifiers, learned weights or peak table.
// Build variants differ only by one final stationary query.
#include <algorithm>
#include <cerrno>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>
using namespace std;
#ifndef COUNT_QUERY
#define COUNT_QUERY 0
#endif

bool readNumber(long long& value) {
    char line[128];
    if (!fgets(line, sizeof(line), stdin)) return false;
    errno = 0; char* end = nullptr; value = strtoll(line, &end, 10);
    if (end == line || errno == ERANGE) return false;
    while (*end && isspace(static_cast<unsigned char>(*end))) ++end;
    return !*end && value >= 0 && value <= 2147483647LL;
}
void emitQuery(int x) {
    if (printf("%d\n", x) < 0 || fflush(stdout)) std::_Exit(0);
}

struct Search {
    static constexpr int STEP = 8;
    static constexpr int WORK_QUERIES = 197; // final return <=198; count variant <=199
    int n, pos = 0, q = 0, direction = 0, turns = 0, far = 0, best = -1;
    int batches = 0, lastInspection = -1000;
    long long value[1000]{};
    bool seen[1000]{};
    vector<int> primary, secondary, records, trace;
    struct Window { int c, lo, hi; bool complete; };
    vector<Window> windows;
    explicit Search(int size): n(size) {}

    bool prefer(int a, int b) const {
        if (b < 0) return true;
        if (value[a] != value[b]) return value[a] > value[b];
        int da = abs(2*a-(n-1)), db = abs(2*b-(n-1));
        return da != db ? da < db : a < b;
    }
    bool allowed(const vector<int>& plan, bool reserveReturn = true) const {
        int at = pos, d = direction, r = turns, count = q;
        for (int x: plan) {
            if (x < 0 || x >= n) return false;
            int nd = (x > at) - (x < at);
            if (nd && d && nd != d) ++r;
            if (nd) d = nd;
            at = x; ++count;
        }
        // One additional change of direction and one query always remain available.
        return count <= (reserveReturn ? WORK_QUERIES : 198) &&
               r <= (reserveReturn ? 5 : 6);
    }
    void move(int x) {
        emitQuery(x); long long y;
        if (!readNumber(y)) std::_Exit(0);
        int d = (x > pos) - (x < pos);
        if (d && direction && d != direction) ++turns;
        if (d) direction = d;
        pos = x; far = max(far, x); ++q;
        value[x] = y; seen[x] = true; trace.push_back(x);
        if (prefer(x, best)) best = x;
    }
    bool get(int x) {
        if (seen[x]) return true;
        if (!allowed({x})) return false;
        move(x); return true;
    }
    static double median(vector<double> a) {
        if (a.empty()) return 0;
        nth_element(a.begin(), a.begin()+a.size()/2, a.end());
        return a[a.size()/2];
    }
    struct Shape {
        double low = 0, range = 0, noise = 0, width = 8, contrast = 0;
        double tail = 0, rebound = 0;
        bool falling = false, flat = false;
    };
    Shape shape(int c) const {
        Shape s; s.low = value[c];
        for (int x: primary) s.low = min(s.low, double(value[x]));
        // A refined peak may exceed every coarse sample.
        s.range = max(0.0, double(value[c])-s.low);
        s.contrast = s.range / max(1.0, double(value[c]));
        vector<double> residual;
        for (size_t i=2; i<primary.size(); ++i) {
            int a=primary[i-2], b=primary[i-1], d=primary[i];
            double prediction = value[a] + (double(value[d])-value[a])*(b-a)/max(1,d-a);
            residual.push_back(abs(double(value[b])-prediction));
        }
        s.noise = median(residual);
        double half = s.low + .5*s.range;
        int left = c;
        for (auto it=primary.rbegin(); it!=primary.rend(); ++it) {
            if (*it >= c) continue;
            left = *it;
            if (value[*it] <= half) break;
        }
        s.width = max(double(STEP), double(c-left));
        vector<double> tail;
        for (auto it=primary.rbegin(); it!=primary.rend() && tail.size()<4; ++it)
            if (*it > c) tail.push_back(double(value[*it]));
        s.tail = tail.empty() ? double(value[c]) : median(tail);
        double minimum = value[c];
        for (int x: primary) if (x > c) minimum = min(minimum, double(value[x]));
        s.rebound = max(0.0, s.tail-minimum);
        s.falling = s.range > 0 && s.tail <= value[c]-max(3*s.noise, .12*s.range);
        s.flat = s.range == 0;
        return s;
    }
    int waitDistance(int c, const Shape& s) const {
        // Spatial distances derive from observed half-width and the O<200 rule.
        // Clean, high-contrast peaks get a shorter verification tail.
        bool clean = s.contrast >= .70 && s.noise <= .035*s.range &&
                     s.tail <= s.low+.18*s.range && s.rebound <= .06*s.range;
        if (clean) return int(min(160.0, max(128.0, 2*s.width)));
        double wait = max(128.0, min(176.0, 3*s.width+32));
        if (s.contrast < .5 || s.noise > .18*s.range || s.rebound > .15*s.range)
            wait = max(wait, 160.0);
        (void)c;
        return int(wait);
    }
    bool fullyRead(int lo, int hi) const {
        for (int x=lo; x<=hi; ++x) if (!seen[x]) return false;
        return true;
    }
    vector<int> ranked(const vector<int>& points) const {
        vector<int> out = points;
        sort(out.begin(), out.end(), [&](int a,int b){return prefer(a,b);});
        out.erase(unique(out.begin(),out.end()),out.end());
        return out;
    }
    vector<int> candidateCenters() const {
        vector<int> out;
        auto add = [&](int c) {
            if (c<0 || c>=n || !seen[c]) return;
            // A hypothesis already >199 behind the farthest visit cannot score.
            if (far-min(n-1,c+STEP) >= 200) return;
            // Nearby centers may have different unread edge points. Only exact
            // duplicate centers are merged; the query planner unions their points.
            for (int y: out) if (y==c) return;
            out.push_back(c);
        };
        add(best);
        // Lists remain independent: a weak sample on one grid is not deleted
        // merely because the other grid has a higher coarse sample.
        auto a=ranked(primary), b=ranked(secondary);
        for (size_t i=0;i<2;++i) {
            if(i<a.size())add(a[i]);
            if(i<b.size())add(b[i]);
        }
        // Keep the two most recently retired primary records as additional proposals.
        int used=0;
        for (auto it=records.rbegin();it!=records.rend() && used<2;++it) {
            if (*it==best) continue;
            add(*it); ++used;
        }
        return out;
    }
    bool phaseSweep() {
        // Revisit the still legally recoverable suffix on the complementary grid.
        // Unlike continuous interleaving, this pays for phase diversity only at
        // an actual stopping decision and can change the local candidate winner.
        if (batches>=2) return false;
        vector<int> plan;
        for(int x=far;x>=max(0,far-199);--x)
            if(x%STEP==6 && !seen[x]) plan.push_back(x);
        if(plan.empty() || q+int(plan.size())+14>WORK_QUERIES) return false;
        if(!allowed(plan)) return false;
        // The following ascending refinement needs another direction change.
        int extraTurn=(direction>0 || direction==0) ? 1:0;
        if(turns+extraTurn+1>5) return false;
        for(int x:plan){move(x);secondary.push_back(x);}
        return true;
    }
    bool refine(bool ascending = false) {
        vector<int> missing, centers = candidateCenters(), chosen;
        bool inPlan[1000]{};
        int cap = min(64, WORK_QUERIES-q); // at most four 16-fresh-point windows
        int rightLimit=min(n-1,max(0,best-STEP)+199);
        for (const Window& w:windows)
            if(w.complete && w.lo<=best && best<=w.hi) rightLimit=min(n-1,best+199);
        for (int c: centers) {
            int lo=max(0,c-STEP), hi=min(n-1,c+STEP);
            if(hi>rightLimit) continue;
            vector<int> extra;
            for (int x=hi;x>=lo;--x) if (!seen[x] && !inPlan[x]) extra.push_back(x);
            if (int(missing.size()+extra.size())>cap) continue;
            chosen.push_back(c);
            for (int x:extra) {inPlan[x]=true;missing.push_back(x);}
        }
        if (missing.empty()) return false;
        if(ascending) sort(missing.begin(),missing.end());
        else sort(missing.rbegin(),missing.rend());
        if (!allowed(missing)) return false;
        for (int x: missing) move(x);
        ++batches;
        for (int c:chosen) {
            int lo=max(0,c-STEP),hi=min(n-1,c+STEP);
            windows.push_back({c,lo,hi,fullyRead(lo,hi)});
        }
        // A complete window is obsolete only if an actually observed preferred
        // point exceeds its exact maximum. Opaque proposals are never so certified.
        return true;
    }
    bool localEvidence() const {
        for (const Window& w: windows) {
            if (!w.complete || best<w.lo || best>w.hi) continue;
            int winner=w.lo; long long low=value[w.lo];
            for (int x=w.lo;x<=w.hi;++x) {
                if (prefer(x,winner)) winner=x;
                low=min(low,value[x]);
            }
            if (winner!=best) continue;
            if ((winner==w.lo && w.lo>0) || (winner==w.hi && w.hi<n-1)) continue;
            for (int x:primary) low=min(low,value[x]);
            bool amplitude=2*(value[winner]-low)>=value[winner] && value[winner]>low;
            bool unimodal=value[winner]>low;
            for (int x=w.lo;x<winner;++x) if(value[x]>value[x+1])unimodal=false;
            for (int x=winner;x<w.hi;++x) if(value[x]<value[x+1])unimodal=false;
            long long side=max(value[max(0,w.c-STEP)],value[min(n-1,w.c+STEP)]);
            bool gain=value[w.c]>=side && value[winner]-value[w.c]>value[w.c]-side;
            if (amplitude || unimodal || gain) return true;
        }
        return false;
    }
    bool canPostponeWeakInspection(const Shape& s) const {
        bool weak=s.contrast<.5 || s.noise>.18*s.range || s.rebound>.15*s.range;
        if(!weak || primary.empty() || urgent())return false;
        int next=primary.back()+STEP;
        if(next>=n)return false;
        // Conditional deadlines only: unknown global truth is NOT available.
        int deadline=n-1;
        auto centers=candidateCenters();
        if(centers.empty())return false;
        for(int c:centers){
            int lo=max(0,c-STEP),hi=min(n-1,c+STEP),anchor=lo;
            if(fullyRead(lo,hi)){
                anchor=lo;for(int x=lo+1;x<=hi;++x)if(prefer(x,anchor))anchor=x;
            }
            deadline=min(deadline,anchor+199);
        }
        if(max(far,next)>deadline)return false;
        // Reserve next actual coarse query, an unchanged phase sweep, up to
        //64 fresh refinement points and the mandatory actual return query.
        int at=pos,d=direction,r=turns,count=q;
        auto step=[&](int x){int nd=(x>at)-(x<at);if(nd&&d&&nd!=d)++r;if(nd)d=nd;at=x;++count;};
        if(!seen[next])step(next);
        int frontier=max(far,next);
        if(batches<2)for(int x=frontier;x>=max(0,frontier-199);--x)
            if(x%STEP==6 && !seen[x])step(x);
        // At most three further reversals for ascending refinement and return,
        // including a first refinement point below the sweep's final position.
        return count+64<=WORK_QUERIES && r+3<=6;
    }
    bool shouldInspect(bool boundary) const {
        if (best<0) return false;
        Shape s=shape(best);
        int lag=far-best;
        if (!boundary && s.range==0) return false;
        if (!boundary && far-lastInspection<32 && !urgent()) return false;
        bool due=boundary || lag>=184 || (lag>=waitDistance(best,s) && s.falling &&
                                         s.rebound<=max(4*s.noise,.20*s.range));
        if(!due)return false;
        if(!boundary && canPostponeWeakInspection(s))return false;
        return true;
    }
    bool accept(bool boundary) const {
        if (best<0) return false;
        if (boundary) return true;
        if (!localEvidence()) return false;
        Shape s=shape(best);
        // This is empirical online evidence, not a global-optimum certificate.
        return far-best>=waitDistance(best,s) && s.falling &&
               s.rebound<=max(4*s.noise,.20*s.range);
    }
    bool urgent() const {
        // c-8+199 is the conservative deadline of an unrefined best bracket.
        int earliest=max(0,best-STEP);
        for (const Window& w:windows)
            if (w.complete && w.lo<=best && best<=w.hi) earliest=best;
        return far+STEP > earliest+199;
    }
    void finish() {
        if (best<0) {move(0);}
        // Actual final query is mandatory even if the answer is cached.
        if (!allowed({best},false)) std::_Exit(3);
        move(best);
        if (COUNT_QUERY) move(best);
    }
    void solve() {
        int primaryBest=-1;
        for (int x=0;x<n;x+=STEP) {
            if (!get(x)) break;
            primary.push_back(x);
            if (prefer(x,primaryBest)) {
                primaryBest=x;records.push_back(x);
            }
            bool boundary=x+STEP>=n;
            if (shouldInspect(boundary)) {
                lastInspection=far;
                bool swept=phaseSweep();
                refine(swept);
                if (accept(boundary)) {finish();return;}
            }
            if (urgent() && localEvidence()) {finish();return;}
        }
        // Exhausted resources must return to a retained observed candidate;
        // jumping to N-1 here would destroy an early winner's overshoot budget.
        refine();
        finish();
    }
};

#ifndef LOCAL_BATCH
int main() {
    setvbuf(stdout,nullptr,_IONBF,0);
    long long n;
    if (!readNumber(n) || n<400 || n>1000) return 0;
    Search s{int(n)};s.solve();
    fputs("DONE\n",stdout);fflush(stdout);return 0;
}
#endif
