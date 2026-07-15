class uart_sequence_DATA extends uvm_sequence #(uart_seq_item);
    `uvm_object_utils(uart_sequence_DATA)
    function new(string name = "uart_sequence_DATA");
        super.new(name);
    endfunction
    virtual task body();
        `uvm_info("SEQ", "Starting directed sequence for DATA", UVM_LOW)
        $display("[UVM_INFO] DATA state hit");
        req = uart_seq_item::type_id::create("req");
        start_item(req);
        // Note: Do not call req.randomize() to avoid Z3 SAT solver dependency in Verilator on Windows
        req.tx_data = 8'hAA;
        req.rx_data = 8'hAA;
        finish_item(req);
    endtask
endclass

class uart_test_directed_DATA extends uart_test_base;
    `uvm_component_utils(uart_test_directed_DATA)
    function new(string name = "uart_test_directed_DATA", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    virtual task run_phase(uvm_phase phase);
        uart_sequence_DATA seq;
        phase.raise_objection(this);
        seq = uart_sequence_DATA::type_id::create("seq");
        seq.start(env.agent.sequencer);
        phase.drop_objection(this);
    endtask
endclass