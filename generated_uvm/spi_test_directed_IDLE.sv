class spi_sequence_IDLE extends uvm_sequence #(spi_seq_item);
    `uvm_object_utils(spi_sequence_IDLE)
    function new(string name = "spi_sequence_IDLE");
        super.new(name);
    endfunction
    virtual task body();
        `uvm_info("SEQ", "Starting directed sequence for IDLE", UVM_LOW)
        $display("[UVM_INFO] IDLE state hit");
        req = spi_seq_item::type_id::create("req");
        start_item(req);
        // Note: Do not call req.randomize() to avoid Z3 SAT solver dependency in Verilator on Windows
        req.mosi = 1'b1;
        req.miso = 1'b1;
        req.sclk = 1'b1;
        req.cs_n = 1'b0;
        finish_item(req);
        #100; // Delay to allow DUT propagation and monitor sampling
    endtask
endclass

class spi_test_directed_IDLE extends spi_test_base;
    `uvm_component_utils(spi_test_directed_IDLE)
    function new(string name = "spi_test_directed_IDLE", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    virtual task run_phase(uvm_phase phase);
        spi_sequence_IDLE seq;
        phase.raise_objection(this);
        seq = spi_sequence_IDLE::type_id::create("seq");
        seq.start(env.agent.sequencer);
        phase.drop_objection(this);
    endtask
endclass