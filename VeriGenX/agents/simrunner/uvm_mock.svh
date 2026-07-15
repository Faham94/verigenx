// Functional Mock UVM classes and macros for Verilator simulations
`ifndef UVM_MOCK_SVH
`define UVM_MOCK_SVH

/* verilator lint_off DECLFILENAME */
/* verilator lint_off EOFNEWLINE */
/* verilator lint_off IMPLICIT */
/* verilator lint_off UNUSED */
/* verilator lint_off BLKSEQ */

// ------------------------------------------------------------------ //
// UVM Global Registry & Helpers                                      //
// ------------------------------------------------------------------ //

typedef class uvm_component;
typedef class uvm_object;
typedef class uvm_agent;
typedef class uvm_analysis_imp;

virtual class uvm_test_wrapper;
    pure virtual function uvm_component create_component(string name, uvm_component parent);
endclass

class uvm_global_registry;
    static uvm_test_wrapper test_registry[string];
    static uvm_component components[$];
    static int errors_count = 0;

    static function void register_test(string name, uvm_test_wrapper wrapper);
        test_registry[name] = wrapper;
    endfunction

    static function void add_component(uvm_component comp);
        components.push_back(comp);
    endfunction

    static function void increment_errors();
        errors_count++;
    endfunction

    static function bit register_test_helper(string name, uvm_test_wrapper wrapper);
        register_test(name, wrapper);
        return 1;
    endfunction
endclass

// ------------------------------------------------------------------ //
// UVM Macros                                                         //
// ------------------------------------------------------------------ //

`define uvm_component_utils(T) \
    class type_id; \
        static function T create(string name="", uvm_component parent=null); \
            T inst = new(name, parent); \
            return inst; \
        endfunction \
    endclass \
    class test_wrapper_``T extends uvm_test_wrapper; \
        virtual function uvm_component create_component(string name, uvm_component parent); \
            T inst = new(name, parent); \
            return inst; \
        endfunction \
    endclass \
    static test_wrapper_``T wrapper_inst_``T; \
    static bit is_registered_``T; \
    static function bit register_helper_``T(); \
        wrapper_inst_``T = new(); \
        return uvm_global_registry::register_test_helper( `"T`", wrapper_inst_``T ); \
    endfunction \
    static bit dummy_reg_``T = register_helper_``T();

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

`define uvm_info(ID, MSG, VERBOSITY) \
    $display("[UVM_INFO] @ %0t | %s: %s", $time, ID, MSG);

`define uvm_error(ID, MSG) \
    begin \
        $display("[UVM_ERROR] @ %0t | %s: %s", $time, ID, MSG); \
        uvm_global_registry::increment_errors(); \
    end

`define uvm_fatal(ID, MSG) \
    begin \
        $display("[UVM_FATAL] @ %0t | %s: %s", $time, ID, MSG); \
        $finish; \
    end

`define uvm_field_int(F, FLAG)

// ------------------------------------------------------------------ //
// UVM Base Classes                                                   //
// ------------------------------------------------------------------ //

typedef class uvm_phase;
typedef class uvm_sequence_item;
typedef class uvm_sequencer;
typedef class uvm_analysis_imp_base;

typedef int uvm_active_passive_enum;
parameter uvm_active_passive_enum UVM_ACTIVE = 0;
parameter uvm_active_passive_enum UVM_PASSIVE = 1;

parameter int UVM_ALL_ON = 0;
parameter int UVM_MEDIUM = 100;
parameter int UVM_LOW = 10;

virtual class uvm_void;
endclass

class uvm_object extends uvm_void;
    string m_name;
    function new(string name="");
        m_name = name;
    endfunction
    virtual function string get_name(); return m_name; endfunction
    virtual function string convert2string(); return ""; endfunction
    virtual function bit compare(uvm_object rhs); return 1; endfunction
    virtual function void copy(uvm_object rhs); endfunction
    virtual function uvm_object clone(); return this; endfunction
endclass

class uvm_report_object extends uvm_object;
    function new(string name=""); super.new(name); endfunction
endclass

class uvm_component extends uvm_report_object;
    uvm_component m_parent;
    function new(string name="", uvm_component parent=null);
        super.new(name);
        m_parent = parent;
        uvm_global_registry::add_component(this);
    endfunction
    virtual function void build_phase(uvm_phase phase); endfunction
    virtual function void connect_phase(uvm_phase phase); endfunction
    virtual task run_phase(uvm_phase phase); endtask
    virtual function void report_phase(uvm_phase phase); endfunction
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
    uvm_sequencer #(REQ, RSP) m_sequencer;

    function new(string name=""); super.new(name); endfunction
    
    virtual task start(uvm_sequencer #(REQ, RSP) sequencer);
        m_sequencer = sequencer;
        this.body();
    endtask

    virtual task body(); endtask
    
    virtual task start_item(uvm_sequence_item item); 
    endtask
    
    virtual task finish_item(uvm_sequence_item item);
        REQ r;
        if ($cast(r, item)) begin
            m_sequencer.put_item(r);
        end else begin
            $display("[UVM_ERROR] finish_item: Cast failed");
        end
    endtask
endclass

class uvm_seq_item_export #(type REQ=uvm_sequence_item, type RSP=REQ) extends uvm_object;
    uvm_object m_sequencer_obj;
    function new(string name=""); super.new(name); endfunction
endclass

class uvm_mailbox #(type T=int) extends uvm_object;
    T queue[$];
    event data_avail;
    
    function new(string name="");
        super.new(name);
    endfunction
    
    virtual task put(T val);
        queue.push_back(val);
        -> data_avail;
    endtask
    
    virtual task get(ref T val);
        while (queue.size() == 0) begin
            @data_avail;
        end
        val = queue.pop_front();
    endtask
    
    virtual function int num();
        return queue.size();
    endfunction
endclass

class uvm_sequencer #(type REQ=uvm_sequence_item, type RSP=REQ) extends uvm_component;
    class type_id;
        static function uvm_sequencer #(REQ, RSP) create(string name="", uvm_component parent=null);
            uvm_sequencer #(REQ, RSP) inst = new(name, parent);
            return inst;
        endfunction
    endclass

    uvm_seq_item_export #(REQ, RSP) seq_item_export;
    uvm_mailbox #(REQ) req_mailbox;
    event item_done_event;

    function new(string name="", uvm_component parent=null);
        super.new(name, parent);
        seq_item_export = new("seq_item_export");
        seq_item_export.m_sequencer_obj = this;
        req_mailbox = new("req_mailbox");
    endfunction
    
    virtual task get_next_item(ref REQ item);
        req_mailbox.get(item);
    endtask

    virtual function void item_done();
        -> item_done_event;
    endfunction

    virtual task put_item(REQ item);
        req_mailbox.put(item);
        @item_done_event;
    endtask
endclass

class uvm_seq_item_pull_port #(type REQ=uvm_sequence_item, type RSP=REQ) extends uvm_object;
    uvm_sequencer #(REQ, RSP) m_sequencer;
    function new(string name=""); super.new(name); endfunction
    virtual function void connect(uvm_seq_item_export #(REQ, RSP) export_port);
        // Bind to sequencer via export port check
        $cast(m_sequencer, export_port.m_sequencer_obj);
    endfunction
    virtual task get_next_item(ref REQ item);
        m_sequencer.get_next_item(item);
    endtask
    virtual function void item_done();
        m_sequencer.item_done();
    endfunction
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
    
    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        // Connect pull port to sequencer automatically for mock if not already connected
        if (seq_item_port.m_sequencer == null && m_parent != null) begin
            // Locate sequencer in agent
            uvm_agent agent;
            if ($cast(agent, m_parent)) begin
                $cast(seqr, agent.sequencer);
                seq_item_port.m_sequencer = seqr;
            end
        end
    endfunction
endclass

class uvm_monitor extends uvm_component;
    function new(string name="", uvm_component parent=null); super.new(name, parent); endfunction
endclass

class uvm_agent extends uvm_component;
    uvm_component sequencer; // Store as generic component reference
    function new(string name="", uvm_component parent=null); super.new(name, parent); endfunction
    virtual function uvm_active_passive_enum get_is_active(); return UVM_ACTIVE; endfunction
endclass

class uvm_scoreboard extends uvm_component;
    function new(string name="", uvm_component parent=null); super.new(name, parent); endfunction
endclass

virtual class uvm_subscriber #(type T=uvm_object) extends uvm_component;
    uvm_analysis_imp #(T, uvm_subscriber #(T)) analysis_export;
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
    int objection_count = 0;
    function new(string name=""); super.new(name); endfunction
    virtual function void raise_objection(uvm_object obj);
        objection_count++;
    endfunction
    virtual function void drop_objection(uvm_object obj);
        objection_count--;
    endfunction
endclass

class uvm_analysis_port #(type T=uvm_object) extends uvm_object;
    uvm_analysis_imp_base #(T) subscribers[$];
    function new(string name="", uvm_component parent=null); super.new(name); endfunction
    virtual function void connect(uvm_analysis_imp_base #(T) imp);
        subscribers.push_back(imp);
    endfunction
    virtual function void write(T t);
        for (int i = 0; i < subscribers.size(); i++) begin
            subscribers[i].write(t);
        end
    endfunction
endclass

virtual class uvm_analysis_imp_base #(type T=uvm_object) extends uvm_object;
    function new(string name=""); super.new(name); endfunction
    pure virtual function void write(T t);
endclass

class uvm_analysis_imp #(type T=uvm_object, type IMP=uvm_component) extends uvm_analysis_imp_base #(T);
    IMP m_parent;
    function new(string name="", IMP parent=null);
        super.new(name);
        m_parent = parent;
    endfunction
    virtual function void write(T t);
        m_parent.write(t);
    endfunction
endclass

class uvm_config_db #(type T=int);
    static T storage[string];
    static function bit get(uvm_component cntxt, string inst_name, string field_name, inout T value);
        if (storage.exists(field_name)) begin
            value = storage[field_name];
            return 1;
        end
        return 0;
    endfunction
    static function void set(uvm_component cntxt, string inst_name, string field_name, T value);
        storage[field_name] = value;
    endfunction
endclass

// ------------------------------------------------------------------ //
// Run Test Task                                                      //
// ------------------------------------------------------------------ //

task run_test(string test_name="");
    string cmd_test_name;
    uvm_phase phase;
    uvm_component test_top;
    
    if (test_name == "") begin
        if (!$value$plusargs("UVM_TESTNAME=%s", cmd_test_name)) begin
            $display("[UVM_FATAL] No +UVM_TESTNAME argument provided.");
            $finish;
        end
        test_name = cmd_test_name;
    end
    
    $display("[UVM_INFO] Starting test: %s", test_name);
    
    if (!uvm_global_registry::test_registry.exists(test_name)) begin
        $display("[UVM_FATAL] Test '%s' not found in registry.", test_name);
        $finish;
    end
    
    test_top = uvm_global_registry::test_registry[test_name].create_component("uvm_test_top", null);
    phase = new("run");
    
    // 1. Build Phase
    $display("[UVM_INFO] Entering Build Phase...");
    test_top.build_phase(phase);
    for (int i = 1; i < uvm_global_registry::components.size(); i++) begin
        uvm_global_registry::components[i].build_phase(phase);
    end
    
    // 2. Connect Phase
    $display("[UVM_INFO] Entering Connect Phase...");
    for (int i = 0; i < uvm_global_registry::components.size(); i++) begin
        uvm_global_registry::components[i].connect_phase(phase);
    end
    
    // 3. Run Phase
    $display("[UVM_INFO] Entering Run Phase...");
    for (int i = 0; i < uvm_global_registry::components.size(); i++) begin
        automatic int idx = i;
        fork
            uvm_global_registry::components[idx].run_phase(phase);
        join_none
    end
    
    // Wait for objections
    #10;
    while (phase.objection_count > 0) begin
        #10;
    end
    
    // 4. Report Phase
    $display("[UVM_INFO] Entering Report Phase...");
    for (int i = 0; i < uvm_global_registry::components.size(); i++) begin
        uvm_global_registry::components[i].report_phase(phase);
    end
    
    $display("[UVM_INFO] Simulation finished (all objections dropped).");
    if (uvm_global_registry::errors_count > 0) begin
        $display("[UVM_ERROR] Simulation FAILED with %0d errors.", uvm_global_registry::errors_count);
    end else begin
        $display("[UVM_INFO] Simulation PASSED.");
    end
    $finish;
endtask

`endif // UVM_MOCK_SVH
