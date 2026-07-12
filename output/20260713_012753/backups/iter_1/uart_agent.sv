class uart_agent extends uvm_agent;

    uvm_sequencer #(uart_seq_item) sequencer;
    uart_driver driver;
    uart_monitor monitor;

    `uvm_component_utils(uart_agent)

    function new(string name = "uart_agent", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        monitor = uart_monitor::type_id::create("monitor", this);
        
        if (get_is_active() == UVM_ACTIVE) begin
            sequencer = uvm_sequencer#(uart_seq_item)::type_id::create("sequencer", this);
            driver = uart_driver::type_id::create("driver", this);
        end
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if (get_is_active() == UVM_ACTIVE) begin
            driver.seq_item_port.connect(sequencer.seq_item_export);
        end
    endfunction

endclass