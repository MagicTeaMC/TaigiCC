#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse
import sys
from typing import Dict, Tuple


class Converter:
    def __init__(self, dict_path: str):
        with open(dict_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.dict_version = data.get('dict_version', 0)
        self.entries = data.get('entries', [])
        
        self.tw_to_zh = {}  # 台文 -> [(華文, 權重), ...]
        self.zh_to_tw = {}  # 華文 -> [(台文, 權重), ...]
        
        for entry in self.entries:
            tw = entry['台文']
            cn = entry['華文']
            weight = entry.get('權重', 0.0)
            
            if tw not in self.tw_to_zh:
                self.tw_to_zh[tw] = []
            self.tw_to_zh[tw].append((cn, weight))
            
            if cn not in self.zh_to_tw:
                self.zh_to_tw[cn] = []
            self.zh_to_tw[cn].append((tw, weight))
    
    def calculate_weight(self, text: str, base_weight: float) -> float:
        length_weight = len(text) * 0.1
        return length_weight + base_weight
    
    def find_best_match(self, text: str, pos: int, dictionary: Dict) -> Tuple[str, str, int]:

        best_match = None
        best_replacement = None
        best_weight = float('-inf')
        best_length = 0
        
        for length in range(1, len(text) - pos + 1):
            substring = text[pos:pos + length]
            
            if substring in dictionary:
                for replacement, base_weight in dictionary[substring]:
                    total_weight = self.calculate_weight(substring, base_weight)
                    
                    if total_weight > best_weight:
                        best_weight = total_weight
                        best_match = substring
                        best_replacement = replacement
                        best_length = length
        
        return best_match, best_replacement, best_length
    
    def convert(self, text: str, mode: str) -> str:
        if mode == 't2c':
            dictionary = self.tw_to_zh
        elif mode == 'c2t':
            dictionary = self.zh_to_tw
        else:
            raise ValueError(f"你欲做啥？不支援的模式: {mode}")
        
        result = []
        pos = 0
        
        while pos < len(text):
            match, replacement, length = self.find_best_match(text, pos, dictionary)
            
            if match:
                result.append(replacement)
                pos += length
            else:
                result.append(text[pos])
                pos += 1
        
        return ''.join(result)


def main():
    parser = argparse.ArgumentParser(
        description='TaigiCC - Taigi-Chinese Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s --mode t2c --text "台文內容" --dict dict.json
  %(prog)s --mode c2t --file input.txt --dict dict.json --output output.txt
        """
    )
    
    parser.add_argument('--mode', '-m', required=True, choices=['t2c', 'c2t'],
                        help='轉換模式: t2c (台文到華文) 或 c2t (華文到台文)')
    parser.add_argument('--dict', '-d', required=True,
                        help='字典檔案路徑 (JSON 格式)')
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--text', '-t',
                            help='直接輸入要轉換的文字')
    input_group.add_argument('--file', '-f',
                            help='輸入檔案路徑')
    
    parser.add_argument('--output', '-o',
                        help='輸出檔案路徑 (不指定則輸出到 stdout)')
    
    args = parser.parse_args()
    
    try:
        converter = Converter(args.dict)
        
        if args.text:
            input_text = args.text
        else:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_text = f.read()
        
        output_text = converter.convert(input_text, args.mode)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"轉換完成，已輸出到: {args.output}", file=sys.stderr)
        else:
            print(output_text)
    
    except FileNotFoundError as e:
        print(f"錯誤: 檔案不存在 - {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"錯誤: JSON 格式錯誤 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"錯誤: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()