// Mock UVM classes and macros for Verilator linting
`ifndef UVM_MOCK_SVH
`define UVM_MOCK_SVH

/* verilator lint_off DECLFILENAME */
/* verilator lint_off EOFNEWLINE */
/* verilator lint_off IMPLICIT */
/* verilator lint_off UNUSED */

`define uvm_component_utils(T) \
    class type_id; \
        static function T create(string name="", uvm_component parent=null); \
            T inst = new(name, parent); \
            return inst; \
        endfunction \
    endclass

`define uvm_object_utils(T) \
    class type_id; \
        static function T create(string name=""); \
            T inst = new(name); \
            return inst; \
        endfunction \
    endclass

`define uvm_object_utils_begin(T) \
    class type_id; \
        static function T create(string name=""); \
            T inst = new(name); \
            return inst; \
        endfunction \
    endclass

`define uvm_object_utils_end

`define uvm_info(ID, MSG, VERBOSITY)
`define uvm_fatal(ID, MSG)
`define uvm_error(ID, MSG)
`define uvm_field_int(F, FLAG)

typedef class uvm_phase;
typedef class uvm_component;
typedef class uvm_sequence_item;
typedef class uvm_object;
typedef class uvm_sequencer;
typedef class uvm_analysis_imp;
typedef class uvm_analysis_imp_base;

typedef int uvm_active_passive_enum;
parameter uvm_active_passive_enum UVM_ACTIVE = 0;
parameter uvm_active_passive_enum UVM_PASSIVE = 1;

parameter int UVM_ALL_ON = 0;
parameter int UVM_MEDIUM = 100;

virtual class uvm_void;
endclass

class uvm_object extends uvm_void;
    function new(string name=""); endfunction
    virtual function string get_name(); return ""; endfunction
    virtual function string convert2string(); return ""; endfunction
    virtual function bit compare(uvm_object rhs); return 1; endfunction
endclass

class uvm_report_object extends uvm_object;
    function new(string name=""); super.new(name); endfunction
endclass

class uvm_component extends uvm_report_object;
    function new(string name="", uvm_component parent=null); super.new(name); endfunction
    virtual function void build_phase(uvm_phase phase); endfunction
    virtual function void connect_phase(uvm_phase phase); endfunction
    virtual function void run_phase(uvm_phase phase); endfunction
endclass

class uvm_sequence_item extends uvm_object;
    function new(string name=""); super.new(name); endfunction
endclass

class uvm_transaction extends uvm_sequence_item;
    function new(string name=""); super.new(name); endfunction
endclass

class uvm_sequence_base extends uvm_sequence_item;
    function new(string name=""); super.new(name); endfunction
endclass

class uvm_sequence #(type REQ=uvm_sequence_item, type RSP=REQ) extends uvm_sequence_base;
    REQ req;
    function new(string name=""); super.new(name); endfunction
    virtual task body(); endtask
    virtual task start_item(uvm_sequence_item item); endtask
    virtual task finish_item(uvm_sequence_item item); endtask
endclass

class uvm_seq_item_export #(type REQ=uvm_sequence_item, type RSP=REQ) extends uvm_object;
    function new(string name=""); super.new(name); endfunction
endclass

class uvm_sequencer #(type REQ=uvm_sequence_item, type RSP=REQ) extends uvm_component;
    uvm_seq_item_export #(REQ, RSP) seq_item_export;
    function new(string name="", uvm_component parent=null);
        super.new(name, parent);
        seq_item_export = new("seq_item_export");
    endfunction
    class type_id;
        static function uvm_sequencer #(REQ, RSP) create(string name="", uvm_component parent=null);
            uvm_sequencer #(REQ, RSP) inst = new(name, parent);
            return inst;
        endfunction
    endclass
endclass

class uvm_seq_item_pull_port #(type REQ=uvm_sequence_item, type RSP=REQ) extends uvm_object;
    function new(string name=""); super.new(name); endfunction
    virtual task get_next_item(ref REQ item); endtask
    virtual function void item_done(); endfunction
    virtual function void connect(uvm_seq_item_export #(REQ, RSP) export_port); endfunction
endclass

class uvm_driver #(type REQ=uvm_sequence_item, type RSP=REQ) extends uvm_component;
    REQ req;
    REQ rsp;
    uvm_sequencer #(REQ, RSP) seqr;
    uvm_seq_item_pull_port #(REQ, RSP) seq_item_port;
    function new(string name="", uvm_component parent=null);
        super.new(name, parent);
        seq_item_port = new("seq_item_port");
    endfunction
    virtual task get_next_item(ref REQ item); endtask
    virtual function void item_done(); endfunction
endclass

class uvm_monitor extends uvm_component;
    function new(string name="", uvm_component parent=null); super.new(name, parent); endfunction
endclass

class uvm_agent extends uvm_component;
    function new(string name="", uvm_component parent=null); super.new(name, parent); endfunction
    virtual function uvm_active_passive_enum get_is_active(); return UVM_ACTIVE; endfunction
endclass

class uvm_scoreboard extends uvm_component;
    function new(string name="", uvm_component parent=null); super.new(name, parent); endfunction
endclass

virtual class uvm_subscriber #(type T=uvm_object) extends uvm_component;
    uvm_analysis_imp #(T, uvm_component) analysis_export;
    function new(string name="", uvm_component parent=null);
        super.new(name, parent);
        analysis_export = new("analysis_export", this);
    endfunction
    pure virtual function void write(T t);
endclass

class uvm_env extends uvm_component;
    function new(string name="", uvm_component parent=null); super.new(name, parent); endfunction
endclass

class uvm_test extends uvm_component;
    function new(string name="", uvm_component parent=null); super.new(name, parent); endfunction
endclass

class uvm_phase extends uvm_object;
    function new(string name=""); super.new(name); endfunction
    virtual task raise_objection(uvm_object obj); endtask
    virtual task drop_objection(uvm_object obj); endtask
endclass

class uvm_analysis_port #(type T=uvm_object) extends uvm_object;
    function new(string name="", uvm_component parent=null); super.new(name); endfunction
    virtual function void write(T t); endfunction
    virtual function void connect(uvm_analysis_imp_base #(T) imp); endfunction
endclass

class uvm_analysis_imp_base #(type T=uvm_object) extends uvm_object;
    function new(string name=""); super.new(name); endfunction
endclass

class uvm_analysis_imp #(type T=uvm_object, type IMP=uvm_component) extends uvm_analysis_imp_base #(T);
    function new(string name="", IMP parent=null); super.new(name); endfunction
endclass

class uvm_config_db #(type T=int);
    static function bit get(uvm_component cntxt, string inst_name, string field_name, inout T value); return 1; endfunction
    static function void set(uvm_component cntxt, string inst_name, string field_name, T value); endfunction
endclass

task run_test(string test_name="");
endtask

`endif // UVM_MOCK_SVH
