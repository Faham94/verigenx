class spi_monitor extends uvm_monitor;

    virtual spi_if vif;
    uvm_analysis_port #(spi_seq_item) ap;

    `uvm_component_utils(spi_monitor)

    function new(string name = "spi_monitor", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap = new("ap", this);
        if (!uvm_config_db#(virtual spi_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("MON", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "monitor_run" %}
        spi_seq_item tx;
        forever begin
            @(posedge vif.clk);
            tx = spi_seq_item::type_id::create("tx"); // spi_seq_item replaced dynamically in caller
            tx.mosi = vif.mosi;
            tx.miso = vif.miso;
            tx.cs_n = vif.cs_n;
            ap.write(tx);
        end
// {% endllm_fill %}
    endtask

endclass