class i2c_sequence_IDLE extends uvm_sequence #(i2c_seq_item);
    `uvm_object_utils(i2c_sequence_IDLE)
    function new(string name = "i2c_sequence_IDLE");
        super.new(name);
    endfunction
    virtual task body();
        `uvm_info("SEQ", "Starting directed sequence for IDLE", UVM_LOW)
        $display("[UVM_INFO] IDLE state hit");
        req = i2c_seq_item::type_id::create("req");
        start_item(req);
        // Note: Do not call req.randomize() to avoid Z3 SAT solver dependency in Verilator on Windows
        req.scl = 1'b1;
        req.sda = 1'b1;
        finish_item(req);
        #100; // Delay to allow DUT propagation and monitor sampling
    endtask
endclass

class i2c_test_directed_IDLE extends i2c_test_base;
    `uvm_component_utils(i2c_test_directed_IDLE)
    function new(string name = "i2c_test_directed_IDLE", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    virtual task run_phase(uvm_phase phase);
        i2c_sequence_IDLE seq;
        phase.raise_objection(this);
        seq = i2c_sequence_IDLE::type_id::create("seq");
        seq.start(env.agent.sequencer);
        phase.drop_objection(this);
    endtask
endclass