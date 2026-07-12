class spi_agent extends uvm_agent;

    uvm_sequencer #(spi_seq_item) sequencer;
    spi_driver driver;
    spi_monitor monitor;

    `uvm_component_utils(spi_agent)

    function new(string name = "spi_agent", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        monitor = spi_monitor::type_id::create("monitor", this);
        
        if (get_is_active() == UVM_ACTIVE) begin
            sequencer = uvm_sequencer#(spi_seq_item)::type_id::create("sequencer", this);
            driver = spi_driver::type_id::create("driver", this);
        end
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if (get_is_active() == UVM_ACTIVE) begin
            driver.seq_item_port.connect(sequencer.seq_item_export);
        end
    endfunction

endclass