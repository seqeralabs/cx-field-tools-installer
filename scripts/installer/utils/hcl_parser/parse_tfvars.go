package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/hashicorp/hcl/v2"
	"github.com/hashicorp/hcl/v2/hclparse"
	"github.com/hashicorp/hcl/v2/hclsyntax"
	ctyjson "github.com/zclconf/go-cty/cty/json"
)

func main() {
	const inputFile = "terraform_hclparser.tfvars"
	const outputFile = "terraform_hclparser.json"

	parser := hclparse.NewParser()
	file, diags := parser.ParseHCLFile(inputFile)
	if diags.HasErrors() {
		fmt.Fprintf(os.Stderr, "Failed to parse file: %s\n", diags.Error())
		os.Exit(1)
	}

	body, ok := file.Body.(*hclsyntax.Body)
	if !ok {
		fmt.Fprintln(os.Stderr, "File body is not hclsyntax.Body")
		os.Exit(1)
	}

	content := make(map[string]interface{})

	for name, attr := range body.Attributes {
		val, diag := attr.Expr.Value(&hcl.EvalContext{})
		if diag.HasErrors() {
			fmt.Fprintf(os.Stderr, "Failed to evaluate %s: %s\n", name, diag.Error())
			os.Exit(1)
		}

		// Marshal with cty JSON encoder
		jsonBytes, err := ctyjson.Marshal(val, val.Type())
		if err != nil {
			fmt.Fprintf(os.Stderr, "cty JSON marshal error: %s\n", err)
			os.Exit(1)
		}

		var decoded interface{}
		if err := json.Unmarshal(jsonBytes, &decoded); err != nil {
			fmt.Fprintf(os.Stderr, "JSON decode error: %s\n", err)
			os.Exit(1)
		}

		content[name] = decoded
	}

	// Final JSON output
	pretty, err := json.MarshalIndent(content, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Final JSON marshal failed: %s\n", err)
		os.Exit(1)
	}

	// Print to stdout
	// fmt.Println(string(pretty))
	fmt.Println("Final JSON written to file:", outputFile)

	// Write to output file
	err = os.WriteFile(outputFile, pretty, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to write output file: %s\n", err)
		os.Exit(1)
	}
}
