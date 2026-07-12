class uart_monitor extends uvm_monitor;

    virtual uart_if vif;
    uvm_analysis_port #(uart_seq_item) ap;

    `uvm_component_utils(uart_monitor)

    function new(string name = "uart_monitor", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap = new("ap", this);
        if (!uvm_config_db#(virtual uart_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("MON", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "monitor_run" %}
        forever begin
            @(posedge vif.clk);
            tx = uart_seq_item::create("tx"); // uart_seq_item replaced dynamically in caller
            tx.tx_data = vif.tx_data;
            tx.rx_data = vif.rx_data;
            ap.write(tx);
        end
// {% endllm_fill %}
    endtask

endclass