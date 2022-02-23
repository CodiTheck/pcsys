import pcsys
# import ioc


class Object(object):
    def __init__(self):
        self.inivalue = None;
        self.value    = None;

    def __str__(self):
        return "inivalue = {}\t\tvalue = {}".format(
            self.inivalue,  
            self.value
        );


class FirstProc(pcsys.Proc):
    def init_f(self, state: object):
        state.inivalue = "FG";
        print(state);
        return state;

    def proc_f(self, state, data):
        print("proc_f 1");
        state.inivalue = 0;
        state.value    = range(20);
        print(state);
        return 20;


class SecondProc(pcsys.Proc):
    def init_f(self, state: object):
        state.inivalue += 1000;
        print(state);
        return state;

    def proc_f(self, state, data):
        print("proc_f 2");
        state.inivalue += 1000;
        state.value = range(100);
        print(state);
        return 10;


class ThirstProc(pcsys.MulProc):
    def init_f(self, state: object):
        print(state.inivalue);
        state.inivalue = range(150000000);

        # mult configuration
        self.dset = state.inivalue;
        self.ndiv = 500;

    def d_proc_f(self, state, dset, dx):
        # print(f"{dx = } {dset = }");
        result = [];

        for x in dx:
            y = dset[x];
            # print(y);
            result.append(y**2);

        return result;

    def proc_f(self, state, results):
        print("proc_f 3");
        print(len(results));

        print(state);
        return 10;


if __name__ == '__main__':
    kernel = pcsys.Kernel();
    p1 = FirstProc();
    p2 = SecondProc();
    p3 = ThirstProc();

    proc_seq1 = pcsys.ProcSeq();
    proc_seq2 = pcsys.ProcSeq();
    proc_seq1.add_proc(p1);
    proc_seq1.add_proc(p2);
    # proc_seq1.add_proc(p3);

    proc_seq2.add_proc(p3);
    # proc_seq2.add_proc(p1);
    proc_seq1.add_proc(proc_seq2);

    state = Object();
    p, q  = kernel.start_proc(proc_seq1, state);
    res = kernel.wait_result(q);

    print();
    print(res);


pass
