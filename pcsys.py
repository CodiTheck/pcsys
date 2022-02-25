import sys
import os
import time
import queue
import random
import logging
import concurrent.futures as cf

from multiprocessing import Process
from multiprocessing import Queue


# PROGRAM CONFIG
STOPONFE = True;
DEBUG    = False;
LOG      = True;


# logger_format = "[%(asctime)s %(msecs)03dms] [PID %(process)d] %(message)s";
# error_logger_format = "[ERROR] [%(asctime)s] [PID %(process)d %(threadName)s] %(message)s";
info_logger_format  = "[%(asctime)s %(msecs)03dms] [PID %(process)d %(threadName)s] %(message)s";

# logging.basicConfig(format=error_logger_format, level=logging.ERROR, datefmt="%I:%M:%S");
logging.basicConfig(format=info_logger_format, level=logging.INFO, datefmt="%I:%M:%S");


def info(message):
    if (LOG is None and DEBUG) or LOG: logging.info(message);
    return message;


class StopProcessing(Exception):
    pass;


class Error(object):
    ## It's used to represent an error obtained, when an 
    ## exception is raised.

    def __init__(self, code=None, message: str=None, args: tuple=(None,)):
        """ Constructor of an error"""
        super(Error, self).__init__();
        assert code is not None or message is not None or args == tuple((None,)) (
            "This instance of Error is not valid."
        );
        self.__message = message;
        self.__code    = code;
        self.__args    = args;

    @property
    def message(self):
        return self.__message;

    @property
    def code(self):
        return self.__code;

    @property
    def args(self):
        return self.__args;

    def show(self):
        if (LOG is None and DEBUG) or LOG: print(self);
        return self;
    
    def __str__(self):
        msg = "[ERROR] ";
        if self.__code is not None:
            msg += "[CDOE {}] ".format(self.__code);
        
        if self.__message is not None:
            msg += "{}".format(self.__message);
        else:
            msg += "{}".format(self.__args);
        
        return msg;


class Logger(object):
    ## 1. It's used to represent the errors log
    ## 2. It's a iterable object instance.
    ## 3. It has a len which equals to the errors count

    def __init__(self,):
        """Contructor of a logger instance"""
        super(Logger, self).__init__();
        self.__errors = []; # this is the errors list

    @property
    def errors(self):
        return self.__errors;

    def err(self, e: Error):
        """Function which add an error in error instance list"""
        self.__errors.append(e);

    def has_errors(self):
        """Function to check if there is an error"""
        return len(self.__errors) > 0;

    def __iter__(self):
        """Define that the object is iterable."""
        return iter(self.__errors);

    def __len__(self):
        """Return the len of errors list."""
        return len(self.__errors);
    
    def __str__(self):
        out = "";
        for e in self.__errors:
            out += "{}\n".format(e);
        
        return out;


class CProcess(Process):
    ## It's used to represent a process with error managment.

    def __init__(self, *args, **kwargs):
        """Constructor of a customized process"""
        super(CProcess, self).__init__(*args, **kwargs);
        self._log = Logger();

    @property
    def logger(self):
        return self._log;


class State(object):
    # Structure of global state for multi-processing
    pass;


class BaseProc(object):
    ## This class is the basic structure of a Processing sequence and
    ## the elementary processing.

    def __init__(self, name=None, stsdef=[0, 1]):
        """Constructor of a basic processing instance"""
        super(BaseProc, self).__init__();
        self.__status_index = 0;    # represents the index of next status to select
        self._local_data = None;    # Local data
        self._stsdef  = stsdef      # contains a definition of all available status
        self._status  = None;       # Status of the processing
        self._state   = None;       # State will be used in the processing (global data)
        self._name    = name if name is not None\
                else str(random.randint(0, round(time.time())));
        
        # Liste of errors detected when the course of the processing
        self._log = Logger();

        # callback methods used when processing start
        # and when processing terminate
        self._on_start_cb = None;
        self._on_done_cb  = None;

    @property
    def local(self):
        return self._local_data;

    @local.setter
    def local(self, value):
        self._local_data = value;
        return value;

    @property
    def name(self):
        return self._name;

    @name.setter
    def name(self, name):
        self._name = name;

    @property
    def state(self):
        return self._state;

    @state.setter
    def state(self, value):
        self._state = value;
        return value;

    @property
    def status(self):
        return self._status;

    @status.setter
    def status(self, value):
        if value in self._stsdef:
            self.__status_index = self._stsdef.index(value) + 1;
            self._status = value;
            return self._status;
        else:
            e = Error(message="[ERROR] This status is not defined for this processing!").show();
            self._log.err(e);
            return False;

    @property
    def logger(self):
        return self._log;

    @property
    def on_start_cb(self):
        return self._on_start_cb;

    @property
    def on_done_cb(self):
        return self._on_done_cb;

    def mut(self):
        """Function that is used to change the processing status"""
        if self.__status_index is not None and self.__status_index < len(self._stsdef):
            self._status = self._stsdef[self.__status_index];
            self.__status_index += 1;
        else:
            self._status = None;
            self.__status_index = 0;

        return self._status;

    def set_on_start_cb(self, callback):
        """Function which defines the callback function which will be used
        when the processing will start."""
        assert callable(callback), (
            "The callback must be a function which accepts 1 argument"
        );
        self._on_start_cb = callback;
        return callback;

    def set_on_done_cb(self, callback):
        """Function which defines the callback function which will be used
        when the processing will terminate."""
        assert callable(callback), (
            "The callback must be a function which accepts 1 argument"
        );
        self._on_done_cb = callback;
        return callback;

    def _exec_f(self, state: object, data: object=None):
        """Function which will be called, when we execute this processing.
        So this object which represent a processing is callable."""
        # we can call the function of processing with the current state received
        # by argument, provided the processing function is defined in this instance.
        assert hasattr(self, 'proc_f'), (
            "The proc_f function is not defined in this processing !"
        );
        assert callable(self.proc_f), (
            "The proc_f must is a callable function."
        );

        # execute the processing function
        result = None;
        result = self.proc_f(state, data);

        # we return the current state
        return result;

    def exec(self, state, args):
        """This function allows to recovery arguments from process queue and
        to pass there to processing function for an execution of processing."""
        # info("Execution of this processing started ...");
        result = self._exec_f(state, args);

        # info("Termited.");
        return state, result;

    def init_f(self, state: object):
        """Function to implement by programmer. This function is called before
        execution of main processing."""
        raise NotImplementedError;


class Proc(BaseProc):
    ## This class represent a elementary processing [O(1)]

    def __init__(self, name=None, stsdef=[0]):
        """Constructor of an elementary processing instance."""
        super(Proc, self).__init__(name, stsdef);

    def proc_f(self, state: object, data: object=None):
        """Function which should be redefined by the programmer.
        It's the function which implements the processing to course."""
        raise NotImplementedError;

    def __iter__(self):
        """Iterator of instruction of this processing"""
        return iter([(self.exec, self._local_data,)]);


class MulProc(Proc):
    ## This class represent a multi-processing implementation [O(n)].
    ## This processing must be executed by a multi-thread loop using thread pool.

    def __init__(self, name=None, stsdef=[0, 1]):
        """Constructor of a multi-processing instance."""
        super(MulProc, self).__init__(name, stsdef);
        # {_d_set} represent the var name which contains the iterable data. 
        # It must not be equal to None, because it's required.
        self._d_set = [];
        self._n_div = 0; # represents the number of division.

    @property
    def dset(self):
        return self._d_set;

    @dset.setter
    def dset(self, dset):
        """Function that is used to define the dataset."""
        self._d_set = dset;
        return dset;

    @property
    def ndiv(self):
        return self._n_div;

    @ndiv.setter
    def ndiv(self, ndv):
        """Function that is used to define the number of division"""
        assert type(ndv) is int, ("The number of division must be an integer type.");
        self._n_div = ndv;
        return ndv;

    def d_proc_f(self, state, dset, dx):
        """Function that is to implement for the thread processing of multi-processing process"""
        raise NotImplementedError;

    def dexc(self, state, args):
        """This function allows to recovery arguments from process queue and
        to pass there to processing function for an execution of processing."""
        dset = args.get('dset');
        dx   = args.get('dx');

        # info(f"Exec d_proc {dx = } is started ...");
        result = self._d_exc_f(state, dset, dx);

        # info(f"d_proc {dx = } done !");
        return state, result;

    def _d_exc_f(self, state: object,  dset: object, dx: list=[]):
        """Function which will be called, when we execute this processing.
        So this object which represent a processing is callable."""
        # we can call the function of processing with the current state received
        # by argument, provided the processing function is defined in this instance.
        assert hasattr(self, 'd_proc_f'), (
            "The proc_f function is not defined in this processing !"
        );
        assert callable(self.d_proc_f), (
            "The proc_f must is a callable function."
        );

        # the following var will contain the returned result
        result = None;
        # execute the processing function
        dt = type(dset);
        kx = [];

        if dt is dict:
            keys = dest.keys();
            for k in dx:
                kx.append(keys[k]);

        elif dt is list or hasattr(dset, '__iter__'):
            kx = dx;

        if len(kx) > 0: info("ELEM PROC [%16d .. %16d] ..." % (kx[0], kx[-1]));
        else: 
            info("NO PROC FOR [%16d .. %16d]" % (0, 0));

        result = self.d_proc_f(state, dset, kx);

        # err = Error(message=e.args[0], args=(e,));
        # print("[ERROR] {}".format(err.message));
        # self.__log.err(e);

        # we return the current state
        if len(kx) > 0: info("ELEM PROC [%16d .. %16d] ... DONE !" % (kx[0], kx[-1]));
        return result;

    def __iter__(self):
        """Function which returns a (dexc(), ddt) list."""
        if self._status == 0:
            assert type(self._n_div) is int, (
                "The number of division must be defined and it must be an integer type."
            );
            assert self._d_set and hasattr(self._d_set, '__iter__'), (
                "The dataset must be not null and iterable type."
            );
            size  = len(self._d_set);
            ndiv  = self._n_div;

            # division
            def f(size, ndiv):
                q1 = int(size / ndiv);
                r  = size - q1 * ndiv;
                s2 = r;
                s1 = ndiv - s2;
                return (s1, q1), (s2, q1 + 1);

            (s1, n1), (s2, n2) = f(size, ndiv);
            k = 0;

            for i in range(s1):
                # info(f'{k = } {len(range(k, (k + n1))) = }');
                yield (self.dexc,
                    {
                        'dset' : self._d_set, 
                        'dx'   : range(k, (k + n1)),
                    },
                );
                k = k + n1;

            for i in range(s2):
                # info(f'{k = } {len(range(k, (k + n2))) = }');
                yield (self.dexc,
                    {
                        'dset' : self._d_set, 
                        'dx'   : range(k, (k + n2)),
                    },
                );
                k = k + n2;

        elif self._status == 1:
            yield (self.exec, self._local_data,);
        else:
            raise StopIteration();


class ProcSeq(BaseProc):
    ## This class represent the structure of a sequence of processings to execute
    ## in a process. This execution is powored by the kernel. 
    ## The kernel is implemented later.
    ## The instance of this class must be iterable.

    def __init__(self, name=None):
        """Constructor of an instance of sequence of processing."""
        super(ProcSeq, self).__init__(name=name);
        self.__procs = [];
        # The above attribut represent a processing instances list.

    @property
    def procs(self):
        return self.__procs;

    def add_proc(self, proc):
        """This recursive function is used to add the instructions in this counter"""
        if type(proc) is list:
            for p in proc: self.add_proc(p);
        else:
            assert isinstance(proc, BaseProc), (
                "This argument must be an processing instance."
            );
            self.__procs.append(proc);
            return proc;

    def init_f(self, state: object):
        """Function that is used for preprocessing program of processing sequence.
        This function can be redefined by the programmer."""
        pass;

    def __iter__(self):
        """Defining of customized iteration."""
        return iter(self.__procs);


class Inst(object):
    ## This object represent an elementary instruction executable by the processor

    def __init__(self, f, args: tuple):
        """Constructor of the elementary executable instruction"""
        super(Inst, self).__init__();

        # We check if the function passed in argument is callable
        assert callable(f), (
            "The `f` argement must be a callable function"
        );
        self.__f = f;
        self.__args = args;

    @property
    def f(self):
        return self.__f;

    @property
    def args(self):
        return self.__args;


class Processor(object):
    # This is the structure of a processor.
    # This object will execute the instructions will receive.

    def __init__(self, cpuc=None):
        """Constructor of a processor"""
        super(Processor, self).__init__();

        # Internalle variables of processor
        self.__status = None;
        # self.__odc    = OrdinalCounter();

        # Defining of CPU count
        # =====================
        #
        # PS: It's butter that the CPU count is left than the CPU count of
        # physical processor
        if cpuc is None: self.__cpu_count = os.cpu_count();
        else:            self.__cpu_count = cpuc;

        # I remove a CPU because the current thread uses one CPU
        self.__cpu_count = self.__cpu_count - 1;
        self.__cpu = cf.ThreadPoolExecutor(max_workers=self.__cpu_count);
        self.__future_map = {};
        info("%16d | CPU count" % (self.__cpu_count,));

        # The callback functions
        self.__eicb = lambda x: x;
        self.__ecb  = lambda y: y;

    def put(self, f, args):
        self.__future_map[self.__cpu.submit(f, *args)] = len(self.__future_map);
        return True;

    def set_eicb(self, cb):
        """Function of end task callback setting"""
        assert callable(cb), (
            "This function is not callable."
        );
        self.__eicb = cb;
        return cb;

    def set_ecb(self, cb):
        """Function of en callback setting"""
        assert callable(cb), (
            "This function is not callable."
        );
        self.__ecb = cb;
        return cb;

    def recr(self):
        for future in cf.as_completed(self.__future_map):
            yield future.result();

    def free(self):
        del self.__cpu;
        return True;


class Kernel(CProcess):
    # This structure represent the kernel. The sheduler of process of processing.
    # His role is to allocate an unique process foreach processing to execute.
    # A kernel is also a process.

    def __init__(self, *args, **kwargs):
        """Contructor of the kernel instance"""
        super(Kernel, self).__init__(*args, **kwargs);
        self.__status  = None;      # The kernel's status
        self.__exqueue = Queue()    # Exchange queue between process
        self.__process = {};        # The process dictionary indexed by their PID 
                                    # powered by this kernel
    @property
    def status(self):
        return self.__status;

    def get_process_ins(q: Queue):
        """Function that is used to return a process instance using his PID
        It's return False, if the process instance is not exists."""
        return self.__process.get(q, False);

    def start_proc(self, proc: ProcSeq, state: object):
        """Function that is used to start a processing in a new process."""
        # if proc is not null, then we can continue
        assert proc is not None, (
            """The `proc` which represents the processing instance must be not None."""
        );

        # we can prepare and start the process of our processing and try to send
        # the initialize state to it.
        q = Queue();
        p = Process(target=Kernel.__start_exec, args=(self, proc, state, q));

        # pid = len(self.__process);
        # self.__process[pid] = p;
        self.__process[q] = p;
        p.start();

        # waite for 10ms second, before to return the process instance 
        # and his queue
        # time.sleep(0.010);
        return p, q;

    def exec_proc(self, proc: ProcSeq, state: object):
        """Function which allows to execute directly a processing"""
        return self.__exec(proc, state);

    def __start_exec(self, procs: ProcSeq, state: object, q: Queue):
        """Function which allows to start execution of processing."""
        state, logger = self.__exec(procs, state);
        del self.__process[q];
        q.put((state, logger));

    def wait_result(self, q: Queue):
        """Function used to wait and get the returned resusult of processing sequence."""
        assert q is not None, (
            "None type is not authorized."
        );
        try:
            # while q.empty(): pass;
            result = q.get();
            q.close();
            del q
            return result;
        except KeyboardInterrupt:
            r = input("\n\n[?] Do you want to exit this program ? [y/n] ");
            if r.lower() == 'y'\
                or r.lower() == 'yes':
                sys.exit(0);

            return False;

    # def __get_insts(self, proc: Proc, state: object):
    #     """This function allows you to extract from a processing the elementaries 
    #     instruction to send to ordinal coounter of our processor."""
    #     # If the processing instance is a MultProc, then we segment it according
    #     # to each element of the dataset.
    #     # Exemple:
    #     # FOR data in dataset
    #     #   proc_f(data);
    #     # 
    #     # If the processing instance is a simple Proc, the we consider the proc_f
    #     # implementation for an elementary instruction.
    #     assert proc is not None, (
    #         "The processing instance passed by argument must be not None."
    #     );

    #     # we define the instruction lists
    #     insts = [];

    #     # in first, we check if the processing is an instance of MultProc
    #     # if it's the case, then we apply the segmentation according to each
    #     # element of the dataset
    #     # if isinstance(proc, MulProc):
    #     #    for data in proc:
    #     #        q = Queue();
    #     #        q.put({'state': initstate, 'dset': data});
    #     #
    #     #        inst = Inst(proc.exec, (q,));
    #     #        insts.append(inst);
    #     #
    #     if isinstance(proc, Proc):
    #         k = 0;
    #         for _f_, args in proc:
    #             assert callable(_f_), (
    #                 "The function returned by processing must be callable."
    #             );

    #             inst = Inst(_f_, (state, args));
    #             insts.append(inst);
    #     else:
    #         raise TypeError(
    #             "The processing instance must be a Proc type."
    #         );

    #     info("Recovery of elementary instruction for ordinal counter... DONE !");
    #     return insts;

    # def __exec_with_processor(self, insts):
    #     """Function which executes an instructions list with a processor instance"""
    #     # we get a new processor instance, and we initialize his ordinal counter
    #     # with elementary instructions.
    #     processor = Processor();
    #     info("Loading of instruction into ordinal counter...");
    #     processor.odc.add_inst(insts);
    #     insts.clear();
    #     del insts;

    #     info("Execution started ...");
    #     return processor.exec();

    def __elreg(self, e: Exception, logger: Logger):
        if not isinstance(e, StopProcessing):
            if len(e.args) > 0: logger.err(Error(message=e.args[0]).show());
            else:
                logger.err(Error(message=f"{str(type(e))} type error is detected.").show());
            
            return logger;
        else:
            raise StopProcessing();

    def __procexf(self, procs: ProcSeq, state: object, processor: Processor, logger: Logger):
        returned = None;
        try:
            returned = procs.init_f(state);
        except Exception as e:
            logger = self.__elreg(e, logger);
            if STOPONFE:
                raise StopProcessing();

        for proc in procs:
            try:
                if isinstance(proc, Proc):
                    # execution of initalization function of processing
                    info(f"[{proc.name}] Processing started ...");
                    returned = proc.init_f(state);
                    proc.local = returned;

                    # we can execution these instructions
                    if proc.on_start_cb is not None:
                        proc.on_start_cb(state);                    

                    # execute instruction
                    # results = self.__exec_with_processor(insts);
                    # state   = results[0];

                    while proc.mut() is not None:
                        # recovery of elementary instruction for ordinal counter
                        info("Recovery of next elementary instructions for ordinal counter ...");
                        # insts = self.__get_insts(proc, state);

                        for _f_, args in proc:
                            # inst = Inst(_f_, (state, args));
                            # insts.append(inst);
                            processor.put(_f_, (state, args));

                        results = [];
                        for st, result in processor.recr():
                            results.append(result);
                            state = st;

                        proc.local = results if len(results) > 1\
                                else results[0];

                        # execute instruction
                        # cstate, results = self.__exec_with_processor(insts);
                        # proc.local = results;

                        info(f"[{proc.name}] Processing terminated.");
                        # time.sleep(0.001);

                    if proc.on_done_cb is not None:
                        proc.on_done_cb(state);

                elif isinstance(proc, ProcSeq):
                    # we recall this function to execute this processing sequence
                    state, logger = self.__procexf(proc, state, processor, logger);
                else:
                    # else the processing instance is not valid
                    # we raise a value exception
                    raise ValueError(
                        "This processing of the processing sequence is not a valid instance."
                    );
            except Exception as e:
                logger = self.__elreg(e, logger);
                if STOPONFE:
                    raise StopProcessing();

        return state, logger;

    def __exec(self, procs: ProcSeq, state: object):
        """Function used to execute a processing squence in a process.
        It receives the processing sequence and the initial state by a queue instance."""
        processor = Processor();
        logger    = Logger();

        try:
            state, logger = self.__procexf(procs, state, processor, logger);
        except StopProcessing:
            info("Processing abort.");

        # we return the current state after to free the processor
        processor.free();
        return state, logger;


# class OrdinalCounter(object):
#     # This structure represent a ordinal counter.
#     # This program is used to submit the instructions into CPU for their execution.

#     def __init__(self):
#         """Constructor of an ordinal counter."""
#         super(OrdinalCounter, self).__init__();
#         self.__insts = queue.Queue();  # represents the initialize instructions queue

#     @property
#     def intsize(self):
#         return self.__insts.qsize();

#     def has_next(self):
#         """Function used to check if instructions list is empty"""
#         return not self.__insts.empty();

#     def add_inst(self, inst: object):
#         """This recursive function is used to add the instructions in this counter"""
#         if hasattr(inst, '__iter__'):
#             for i in inst: self.add_inst(i);
#         else:
#             assert isinstance(inst, Inst), (
#                 "This argument must be an instruction instance."
#             );
#             self.__insts.put(inst);
#             return inst;

#     def fetch(self, tpe: cf.ThreadPoolExecutor):
#         """Function that is used to return the instructions formated for 
#         the tread pool executor"""
#         inst_map = {};
#         index    = 0;

#         while not self.__insts.empty():
#             # while queue is not empty, we recovery new instruction instance
#             # that submit to pool thread executor
#             inst = self.__insts.get();
#             args = inst.args;
#             f    = inst.f; 
#             g    = tpe.submit(f, *args);
#             inst_map[g] = index;
#             index += 1;

#         return inst_map;



pass;
