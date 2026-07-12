class uart_driver extends uvm_driver #(uart_seq_item);

    virtual uart_if vif;

    `uvm_component_utils(uart_driver)

    function new(string name = "uart_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual uart_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("DRV", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "driver_reset" %}
        vif.cb.rst_n <= 0;
        #100;
        vif.cb.rst_n <= 1;
// {% endllm_fill %}

        forever begin
            seq_item_port.get_next_item(req);
            // {% llm_fill "driver_drive_item" %}
        @(posedge vif.clk);
            vif.cb.tx_data <= req.tx_data;
        #10;
// {% endllm_fill %}
            seq_item_port.item_done();
        end
    endtask

endclass