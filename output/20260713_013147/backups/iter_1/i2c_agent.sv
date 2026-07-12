class i2c_agent extends uvm_agent;

    uvm_sequencer #(i2c_seq_item) sequencer;
    i2c_driver driver;
    i2c_monitor monitor;

    `uvm_component_utils(i2c_agent)

    function new(string name = "i2c_agent", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        monitor = i2c_monitor::type_id::create("monitor", this);
        
        if (get_is_active() == UVM_ACTIVE) begin
            sequencer = uvm_sequencer#(i2c_seq_item)::type_id::create("sequencer", this);
            driver = i2c_driver::type_id::create("driver", this);
        end
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if (get_is_active() == UVM_ACTIVE) begin
            driver.seq_item_port.connect(sequencer.seq_item_export);
        end
    endfunction

endclass