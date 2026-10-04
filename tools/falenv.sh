#!/bin/zsh
# Source this to export FAL_KEY from ~/.fal/.env.rtf (an RTF file containing
# a line like `fal_api=...` or `fal_api ...`). Never prints the key.
_fal_txt=$(textutil -convert txt -stdout "$HOME/.fal/.env.rtf" 2>/dev/null)
_fal_line=$(printf '%s\n' "$_fal_txt" | grep -i 'fal_api' | head -1)
# take everything after the first '=' or whitespace following fal_api
FAL_KEY=$(printf '%s' "$_fal_line" | sed -E 's/.*fal_api[[:space:]]*[=:]?[[:space:]]*//i' | tr -d '[:space:]"'"'" )
if [ -z "$FAL_KEY" ]; then
  echo "falenv: could not extract fal_api from ~/.fal/.env.rtf" >&2
  return 1 2>/dev/null || exit 1
fi
export FAL_KEY
echo "falenv: FAL_KEY exported (${#FAL_KEY} chars)" >&2
unset _fal_txt _fal_line
