class uart_sequence_IDLE extends uvm_sequence #(uart_seq_item);
    `uvm_object_utils(uart_sequence_IDLE)
    function new(string name = "uart_sequence_IDLE");
        super.new(name);
    endfunction
    virtual task body();
        `uvm_info("SEQ", "Starting directed sequence for IDLE", UVM_LOW)
        $display("[UVM_INFO] IDLE state hit");
        req = uart_seq_item::type_id::create("req");
        start_item(req);
        // Note: Do not call req.randomize() to avoid Z3 SAT solver dependency in Verilator on Windows
        req.tx_data = 8'hAA;
        req.rx_data = 8'hAA;
        finish_item(req);
    endtask
endclass

class uart_test_directed_IDLE extends uart_test_base;
    `uvm_component_utils(uart_test_directed_IDLE)
    function new(string name = "uart_test_directed_IDLE", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    virtual task run_phase(uvm_phase phase);
        uart_sequence_IDLE seq;
        phase.raise_objection(this);
        seq = uart_sequence_IDLE::type_id::create("seq");
        seq.start(env.agent.sequencer);
        phase.drop_objection(this);
    endtask
endclass