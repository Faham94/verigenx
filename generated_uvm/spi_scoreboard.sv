// Reference model base class for injection
class spi_ref_model extends uvm_object;
    `uvm_object_utils(spi_ref_model)

    function new(string name = "spi_ref_model");
        super.new(name);
    endfunction

    // {% llm_fill "ref_model_predict" %}
    virtual function void predict(spi_seq_item item, ref spi_seq_item expected);
        expected = spi_seq_item::type_id::create("expected");
        // Predict next expected outputs based on inputs
    endfunction
// {% endllm_fill %}
endclass


class spi_scoreboard extends uvm_scoreboard;

    uvm_analysis_imp #(spi_seq_item, spi_scoreboard) item_export;
    spi_ref_model ref_model;

    `uvm_component_utils(spi_scoreboard)

    function new(string name = "spi_scoreboard", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        item_export = new("item_export", this);
        
        // Configuration DB retrieval of injectable reference model
        if (!uvm_config_db#(spi_ref_model)::get(this, "", "ref_model", ref_model)) begin
            `uvm_info("SB", "No reference model injected. Creating default reference model.", UVM_MEDIUM)
            ref_model = spi_ref_model::type_id::create("ref_model");
        end
    endfunction

    virtual function void write(spi_seq_item item);
        // {% llm_fill "scoreboard_write" %}
        spi_seq_item expected;
        ref_model.predict(item, expected);
        if (!item.compare(expected)) begin
            `uvm_error("SB_MISMATCH", $sformatf("Transaction mismatch! Actual: %s, Expected: %s", item.convert2string(), expected.convert2string()))
        end else begin
            `uvm_info("SB_MATCH", $sformatf("Transaction match: %s", item.convert2string()), UVM_MEDIUM)
        end
// {% endllm_fill %}
    endfunction

endclass